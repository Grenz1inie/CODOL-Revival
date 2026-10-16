import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.program.model.listing.Function;
import java.nio.file.Files;
import java.nio.file.Path;
public class DumpConsoleFunctions extends GhidraScript {
    public void run() throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        StringBuilder out = new StringBuilder();
        long[] entries = {0x474310,0x49c870,0x49ca70,0x4a6d10,0x4a6d60,0x50f2c0,
                          0x67ee40,0x7f6330,0xb8d050,0x776480,0x67e8e0};
        for (long entry : entries) {
            disassemble(toAddr(entry));
            Function fn = getFunctionAt(toAddr(entry));
            if (fn == null) fn = createFunction(toAddr(entry), "consumer_" + Long.toHexString(entry));
            out.append("\nADDRESS ").append(Long.toHexString(entry)).append("\n");
            if (fn == null) { out.append("unavailable\n"); continue; }
            var result = decompiler.decompileFunction(fn, 15, monitor);
            out.append(result.decompileCompleted() ? result.getDecompiledFunction().getC() : result.getErrorMessage());
        }
        Files.writeString(Path.of(getScriptArgs()[0]), out.toString());
        decompiler.dispose();
    }
}
