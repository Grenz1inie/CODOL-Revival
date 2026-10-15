// Run with Ghidra -noanalysis -readOnly -deleteProject. Standalone evidence, not REA Evidence.
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.*;
import com.google.gson.GsonBuilder;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

public class ExportFocusedFunctions extends GhidraScript {
    public void run() throws Exception {
        String[] args = getScriptArgs();
        Path output = Path.of(args[0]);
        String[] selectors = Arrays.stream(args).skip(1).flatMap(s -> Arrays.stream(s.split(","))).toArray(String[]::new);
        Map<String, Object> report = new LinkedHashMap<>();
        report.put("producer", "standalone-ghidra-focused-script");
        report.put("ghidra_version", ghidra.framework.Application.getApplicationVersion());
        report.put("binary_sha256", currentProgram.getExecutableSHA256());
        report.put("image_base", currentProgram.getImageBase().toString());
        report.put("analysis_mode", "Explicit disassembly and function creation; whole-program auto-analysis disabled");
        report.put("limitations", List.of("Not a REA Evidence record.",
            "Weaker type and function-boundary recovery than default whole-program analysis.",
            "Signatures and register inputs may be inaccurate; inspect retained instructions.",
            "Direct call targets only; unresolved indirect calls are not represented."));
        List<Map<String, Object>> items = new ArrayList<>();
        report.put("items", items);
        for (String selector : selectors) {
            Address entry = toAddr(selector);
            if (getInstructionAt(entry) == null) disassemble(entry);
            if (getFunctionAt(entry) == null) createFunction(entry, null);
        }
        DecompInterface decompiler = new DecompInterface();
        decompiler.setOptions(new DecompileOptions());
        decompiler.toggleCCode(true);
        decompiler.toggleSyntaxTree(true);
        if (!decompiler.openProgram(currentProgram)) throw new IllegalStateException(decompiler.getLastMessage());
        try {
            for (String selector : selectors) {
                Map<String, Object> item = new LinkedHashMap<>();
                item.put("requested_address", selector);
                Function function = getFunctionAt(toAddr(selector));
                if (function == null) {
                    item.put("status", "no-function");
                } else {
                    item.put("address", "0x" + function.getEntryPoint().toString());
                    item.put("name", function.getName());
                    item.put("body", function.getBody().toString());
                    List<String> instructions = new ArrayList<>();
                    Set<String> targets = new TreeSet<>();
                    for (Instruction ins : currentProgram.getListing().getInstructions(function.getBody(), true)) {
                        instructions.add(ins.getAddress() + " " + ins.toString());
                        if (ins.getFlowType().isCall()) for (Address a : ins.getFlows()) targets.add("0x" + a.toString());
                    }
                    item.put("instructions", instructions);
                    item.put("direct_call_targets", targets);
                    DecompileResults result = decompiler.decompileFunction(function, 90, monitor);
                    item.put("status", result.decompileCompleted() ? "ok" : "failed");
                    item.put("diagnostic", result.getErrorMessage());
                    if (result.decompileCompleted()) item.put("pseudocode", result.getDecompiledFunction().getC());
                }
                items.add(item);
                Files.writeString(output, new GsonBuilder().setPrettyPrinting().create().toJson(report), StandardCharsets.UTF_8);
                println("EXPORTED " + selector + " " + item.get("status"));
            }
        } finally { decompiler.dispose(); }
    }
}
