// Export selected native functions after correcting inferred no-return boundaries.
// Analysis metadata only; the input executable is never modified.
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import java.nio.file.Files;
import java.nio.file.Path;

public class ExportNative319 extends GhidraScript {
    public void run() throws Exception {
        String[] args = getScriptArgs();
        Path output = Path.of(args[0]);
        Files.createDirectories(output);
        for (Function function : currentProgram.getFunctionManager().getFunctions(true)) {
            if (function.hasNoReturn()) function.setNoReturn(false);
        }
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        try {
            for (int i = 1; i < args.length; i++) {
                Address entry = toAddr(args[i]);
                disassemble(entry);
                Function function = getFunctionAt(entry);
                if (function == null) function = createFunction(entry, "recovered_" + args[i]);
                if (function == null) throw new IllegalStateException("No function at " + entry);
                DecompileResults result = decompiler.decompileFunction(function, 60, monitor);
                if (!result.decompileCompleted()) throw new IllegalStateException(result.getErrorMessage());
                Files.writeString(output.resolve(args[i] + ".c"), result.getDecompiledFunction().getC());
                println("EXPORTED " + entry + " " + function.getName());
            }
        } finally {
            decompiler.dispose();
        }
    }
}
