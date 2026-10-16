use std::{env,path::Path};

fn run()->Result<(),String> {
    let args:Vec<String>=env::args().skip(1).collect();
    let option=|name:&str|args.windows(2).find(|a|a[0]==name).map(|a|a[1].as_str()).ok_or_else(||format!("missing {name}"));
    match args.first().map(String::as_str) {
        Some("replay")=>{
            let result=codol_match::runtime::replay(Path::new(option("--package")?),Path::new(option("--scenario")?))?;
            println!("{}",result);Ok(())
        },
        Some("serve")=>codol_match::server::serve(Path::new(option("--package")?),
            option("--port").unwrap_or("28970").parse().map_err(|_|"invalid UDP port")?),
        _=>Err("usage: codol-match {replay|serve} --package DIR [--scenario FILE] [--port PORT]".into()),
    }
}
fn main() {if let Err(error)=run() {eprintln!("{error}");std::process::exit(1);}}
