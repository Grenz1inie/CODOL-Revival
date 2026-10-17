// 3.19 CM319 collision reader and C/T/M sweep protocol. No game addresses here.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using V = std::array<float, 3>;
struct Plane { V n; float d; };
struct Trace { float fraction = 1; V normal{{0,0,0}}; bool solid = false, all = false; };
struct Shape { V lo, hi; uint32_t contents; std::vector<Plane> planes, capsule; std::vector<V> vertices; };
static float dot(V a, V b) { return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]; }
static V add(V a, V b) { return {{a[0]+b[0], a[1]+b[1], a[2]+b[2]}}; }
static V mul(V a, float b) { return {{a[0]*b, a[1]*b, a[2]*b}}; }
static V sub(V a, V b) { return add(a, mul(b,-1)); }
static V cross(V a, V b) { return {{a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]}}; }
static const V axes[] = {{{1,0,0}}, {{0,1,0}}, {{0,0,1}}};

class Records {
    std::vector<unsigned char> bytes;
    std::map<uint32_t, std::pair<size_t,size_t>> blocks;
public:
    const unsigned char *header;
    explicit Records(const char *path) {
        std::ifstream file(path, std::ios::binary | std::ios::ate);
        auto length = file.tellg();
        if (length < 268 || length > 256*1024*1024) throw std::runtime_error("Invalid CM319 size");
        bytes.resize(static_cast<size_t>(length));
        file.seekg(0); file.read(reinterpret_cast<char*>(bytes.data()), bytes.size());
        if (!file || std::memcmp(bytes.data(), "CM319", 5)) throw std::runtime_error("Invalid CM319 header");
        header = bytes.data()+12;
        for (size_t offset=268; offset<bytes.size();) {
            if (bytes.size()-offset<8) throw std::runtime_error("Truncated CM319 record");
            uint32_t address = word(bytes.data()+offset), size = word(bytes.data()+offset+4);
            offset += 8;
            if (!size || size>bytes.size()-offset || uint64_t(address)+size>0x100000000ULL || blocks.count(address))
                throw std::runtime_error("Invalid CM319 record");
            blocks[address] = {offset,size}; offset += size;
        }
    }
    static uint32_t word(const unsigned char *p) { uint32_t v; std::memcpy(&v,p,4); return v; }
    static uint16_t half(const unsigned char *p) { uint16_t v; std::memcpy(&v,p,2); return v; }
    static float real(const unsigned char *p) {
        float v; std::memcpy(&v,p,4);
        if (!std::isfinite(v)) throw std::runtime_error("Nonfinite CM319 geometry");
        return v;
    }
    static V vector(const unsigned char *p) { return {{real(p),real(p+4),real(p+8)}}; }
    const unsigned char *at(uint32_t address, size_t length) const {
        auto item = blocks.upper_bound(address);
        if (item == blocks.begin()) throw std::runtime_error("Missing CM319 block");
        --item;
        size_t shift = address-item->first;
        if (shift>item->second.second || length>item->second.second-shift) throw std::runtime_error("Short CM319 block");
        return bytes.data()+item->second.first+shift;
    }
    uint32_t h(size_t offset) const { return word(header+offset); }
};

static void support(std::vector<Plane> &out, V direction, const std::vector<V> &vertices) {
    float length = std::sqrt(dot(direction,direction));
    if (length<0.0001f) return;
    direction=mul(direction,1/length);
    float distance=-1e30f;
    for (V vertex:vertices) distance=std::max(distance,dot(vertex,direction));
    out.push_back({direction,distance});
}

static std::vector<Plane> rounded(const std::vector<V> &normals, const std::vector<V> &vertices) {
    std::vector<Plane> result;
    for (V n:normals) {
        float length=std::sqrt(dot(n,n));
        if (length<0.0001f) continue;
        n=mul(n,1/length);
        bool duplicate=false;
        for (const Plane &p:result) if (dot(p.n,n)>0.9999f) duplicate=true;
        if (!duplicate) support(result,n,vertices);
    }
    size_t count=result.size();
    for (size_t i=0;i<count;i++) for (size_t j=i+1;j<count;j++) {
        Plane a=result[i], b=result[j];
        if (dot(a.n,b.n)>0.98f) continue;
        size_t shared=0;
        for (V v:vertices) if (std::fabs(dot(a.n,v)-a.d)<0.02f && std::fabs(dot(b.n,v)-b.d)<0.02f) shared++;
        if (shared>1) for (float weight:{0.25f,0.5f,0.75f})
            support(result,add(mul(a.n,1-weight),mul(b.n,weight)),vertices);
    }
    return result;
}

static void brush_hull(Shape &shape) {
    std::vector<V> vertices, normals;
    const auto &planes=shape.planes;
    for (const Plane &p:planes) normals.push_back(p.n);
    for (size_t i=0;i<planes.size();i++) for (size_t j=i+1;j<planes.size();j++)
        for (size_t k=j+1;k<planes.size();k++) {
            Plane a=planes[i],b=planes[j],c=planes[k];
            V bc=cross(b.n,c.n); float determinant=dot(a.n,bc);
            if (std::fabs(determinant)<1e-6f) continue;
            V v=mul(add(add(mul(bc,a.d),mul(cross(c.n,a.n),b.d)),mul(cross(a.n,b.n),c.d)),1/determinant);
            bool inside=true;
            for (const Plane &p:planes) if (dot(v,p.n)>p.d+0.01f) { inside=false; break; }
            if (inside) vertices.push_back(v);
        }
    shape.capsule=vertices.size()>=4 ? rounded(normals,vertices) : planes;
}

static void clip(const std::vector<Plane> &planes, V start, V end, V mins, V maxs, bool capsule, Trace &trace) {
    float enter=-1, leave=1; V normal{{0,0,0}}; bool starts_out=false, ends_out=false;
    for (const Plane &p:planes) {
        float offset=0;
        if (capsule) offset=std::min((mins[2]+maxs[0])*p.n[2],(maxs[2]-maxs[0])*p.n[2])-maxs[0];
        else for (int i=0;i<3;i++) offset+=(p.n[i]<0 ? maxs[i] : mins[i])*p.n[i];
        float distance=p.d-offset, a=dot(start,p.n)-distance, b=dot(end,p.n)-distance;
        starts_out |= a>0; ends_out |= b>0;
        if (a>0 && b>0 && (b>=0.125f || a<=b)) return;
        if (a<=0 && b<=0) continue;
        if (a>b) {
            float t=std::max(0.f,(a-0.125f)/(a-b));
            if (t>enter) { enter=t; normal=p.n; }
        } else leave=std::min(leave,std::min(1.f,(a+0.125f)/(a-b)));
    }
    if (!starts_out) {
        trace.solid=true;
        if (!ends_out) { trace.all=true; trace.fraction=0; }
    } else if (enter<leave && enter>-1 && enter<trace.fraction) {
        trace.fraction=enter; trace.normal=normal;
    }
}

class World {
    std::vector<Shape> brushes, triangles;
    using Cell = std::pair<int,int>;
    std::map<Cell,std::vector<size_t>> brush_grid, tri_grid;
    static void index(std::map<Cell,std::vector<size_t>> &grid,const Shape &s,size_t id,int size) {
        int x0=std::floor(s.lo[0]/size),x1=std::floor(s.hi[0]/size);
        int y0=std::floor(s.lo[1]/size),y1=std::floor(s.hi[1]/size);
        if (int64_t(x1-x0+1)*(y1-y0+1)>1000000) throw std::runtime_error("Oversized CM319 bounds");
        for (int y=y0;y<=y1;y++) for (int x=x0;x<=x1;x++) grid[{x,y}].push_back(id);
    }
public:
    explicit World(const char *path) {
        Records r(path);
        uint32_t plane_count=r.h(8),plane_address=r.h(12),brush_count=Records::half(r.header+0x38);
        const auto *planes=r.at(plane_address,size_t(plane_count)*20);
        const auto *data=r.at(r.h(0x3c),size_t(brush_count)*36);
        const auto *bounds=r.at(r.h(0x40),size_t(brush_count)*24);
        const auto *contents=r.at(r.h(0x44),size_t(brush_count)*4);
        for (size_t i=0;i<brush_count;i++) {
            Shape s; V center=Records::vector(bounds+i*24),half=Records::vector(bounds+i*24+12);
            s.lo=sub(center,half);s.hi=add(center,half);s.contents=Records::word(contents+i*4);
            for (int axis=0;axis<3;axis++) {
                if (half[axis]<0) throw std::runtime_error("Invalid CM319 brush bounds");
                s.planes.push_back({axes[axis],s.hi[axis]});
                s.planes.push_back({mul(axes[axis],-1),-s.lo[axis]});
            }
            size_t side_count=Records::half(data+i*36);
            if (side_count>256) throw std::runtime_error("Oversized CM319 brush");
            if (side_count) {
                const auto *sides=r.at(Records::word(data+i*36+4),side_count*8);
                for (size_t j=0;j<side_count;j++) {
                    uint32_t pointer=Records::word(sides+j*8);
                    if (pointer<plane_address || (pointer-plane_address)%20 || (pointer-plane_address)/20>=plane_count)
                        throw std::runtime_error("Invalid CM319 plane index");
                    const auto *p=planes+pointer-plane_address;
                    s.planes.push_back({Records::vector(p),Records::real(p+12)});
                }
            }
            index(brush_grid,s,brushes.size(),256); brushes.push_back(std::move(s));
        }
        uint32_t vertex_count=r.h(0x64),triangle_count=r.h(0x6c);
        const auto *vertices=r.at(r.h(0x68),size_t(vertex_count)*12);
        const auto *indices=r.at(r.h(0x70),size_t(triangle_count)*6);
        if (triangle_count>4000000) throw std::runtime_error("Oversized CM319 triangles");
        std::vector<uint32_t> masks(triangle_count,1);
        if (r.h(0x10) && r.h(0x80) && r.h(0x88)) {
            const auto *materials=r.at(r.h(0x14),size_t(r.h(0x10))*12);
            const auto *partitions=r.at(r.h(0x84),size_t(r.h(0x80))*12);
            const auto *trees=r.at(r.h(0x8c),size_t(r.h(0x88))*32);
            for (uint32_t i=0;i<r.h(0x88);i++) {
                const auto *t=trees+i*32; uint32_t partition=Records::word(t+28);uint16_t material=Records::half(t+12);
                if (Records::half(t+14) || partition>=r.h(0x80) || material>=r.h(0x10)) continue;
                const auto *p=partitions+partition*12; uint32_t first=Records::word(p+4);
                for (uint32_t j=first;j<uint64_t(first)+p[0] && j<triangle_count;j++) masks[j]=Records::word(materials+material*12+8);
            }
        }
        for (uint32_t i=0;i<triangle_count;i++) {
            if (!(masks[i]&0x10001)) continue;
            Shape s;s.contents=masks[i];
            for (int j=0;j<3;j++) {
                uint16_t v=Records::half(indices+i*6+j*2);
                if (v>=vertex_count) throw std::runtime_error("Invalid CM319 vertex index");
                s.vertices.push_back(Records::vector(vertices+v*12));
            }
            V n=cross(sub(s.vertices[1],s.vertices[0]),sub(s.vertices[2],s.vertices[0]));
            float length=std::sqrt(dot(n,n)); if (length<1e-6f) continue;
            n=mul(n,1/length); if (n[2]<0) n=mul(n,-1);
            for (int axis=0;axis<3;axis++) {
                s.lo[axis]=std::min({s.vertices[0][axis],s.vertices[1][axis],s.vertices[2][axis]});
                s.hi[axis]=std::max({s.vertices[0][axis],s.vertices[1][axis],s.vertices[2][axis]});
            }
            std::vector<V> normals{n,mul(n,-1)}, prism=s.vertices;
            for (V v:s.vertices) prism.push_back(sub(v,n));
            support(s.planes,n,prism);support(s.planes,mul(n,-1),prism);
            for (V axis:axes) for (V direction:{axis,cross(axis,n)}) {
                support(s.planes,direction,prism);support(s.planes,mul(direction,-1),prism);
            }
            for (int j=0;j<3;j++) {
                V edge=sub(s.vertices[(j+1)%3],s.vertices[j]);
                V direction=cross(edge,n);
                if (dot(sub(s.vertices[(j+2)%3],s.vertices[j]),direction)>0) direction=mul(direction,-1);
                normals.push_back(direction);
                for (V axis:axes) {
                    V a=cross(edge,axis);support(s.planes,a,prism);support(s.planes,mul(a,-1),prism);
                }
            }
            for (V axis:axes) { normals.push_back(axis);normals.push_back(mul(axis,-1)); }
            s.capsule=rounded(normals,prism);
            index(tri_grid,s,triangles.size(),128);triangles.push_back(std::move(s));
        }
    }
    void ready() const { std::printf("READY %zu %zu\n",brushes.size(),triangles.size()); }
    Trace trace(V start,V end,V mins,V maxs,bool capsule,bool mantle) {
        Trace result;V lo,hi;
        for (int i=0;i<3;i++) { lo[i]=std::min(start[i],end[i])+mins[i]-1;hi[i]=std::max(start[i],end[i])+maxs[i]+1; }
        for (int kind=0;kind<(mantle?1:2);kind++) {
            auto &shapes=kind?triangles:brushes;auto &grid=kind?tri_grid:brush_grid;int size=kind?128:256;
            std::vector<bool> visited(shapes.size(),false);
            int x0=std::floor(lo[0]/size),x1=std::floor(hi[0]/size),y0=std::floor(lo[1]/size),y1=std::floor(hi[1]/size);
            if (int64_t(x1-x0+1)*(y1-y0+1)>1000000) throw std::runtime_error("Oversized sweep");
            for (int y=y0;y<=y1;y++) for (int x=x0;x<=x1;x++) {
                auto cell=grid.find({x,y});if (cell==grid.end()) continue;
                for (size_t id:cell->second) {
                    if (visited[id]) continue;visited[id]=true;Shape &s=shapes[id];
                    if (!(s.contents & (mantle?0x1000000:0x10001))) continue;
                    bool overlap=true;for (int a=0;a<3;a++) if (hi[a]<s.lo[a] || lo[a]>s.hi[a]) overlap=false;
                    if (!overlap) continue;
                    if (capsule && s.capsule.empty()) brush_hull(s);
                    clip(capsule?s.capsule:s.planes,start,end,mins,maxs,capsule,result);
                    if (result.all) return result;
                }
            }
        }
        return result;
    }
};

int main(int argc,char **argv) {
    if (argc!=2) return 2;
    try {
        World world(argv[1]);std::setvbuf(stdout,nullptr,_IONBF,0);world.ready();
        char line[512];
        while (std::fgets(line,sizeof(line),stdin)) {
            std::istringstream input(line);char mode;input>>mode;std::vector<float> values;float value;
            while (input>>value) values.push_back(value);
            size_t count=mode=='C'?9:mode=='T'?12:mode=='M'?6:0;
            if (!count || values.size()!=count || std::any_of(values.begin(),values.end(),[](float f){return !std::isfinite(f) || std::fabs(f)>10000000;})) {
                std::puts("ERR parse");continue;
            }
            V start{{values[0],values[1],values[2]}},end{{values[3],values[4],values[5]}};
            V mins{{-.1f,-.1f,0}},maxs{{.1f,.1f,70}};
            if (mode=='C') { mins={{-values[6],-values[6],values[7]}};maxs={{values[6],values[6],values[8]}}; }
            if (mode=='T') { mins={{values[6],values[7],values[8]}};maxs={{values[9],values[10],values[11]}}; }
            bool valid=true;for (int i=0;i<3;i++) if (mins[i]>maxs[i]) valid=false;
            if (!valid) { std::puts("ERR bounds");continue; }
            Trace t=world.trace(start,end,mins,maxs,mode=='C',mode=='M');
            std::printf("%.6f %.4f %.4f %.4f %d %d\n",t.fraction,t.normal[0],t.normal[1],t.normal[2],t.solid,t.all);
        }
        return 0;
    } catch (const std::exception &error) { std::fprintf(stderr,"collision319: %s\n",error.what());return 3; }
}
