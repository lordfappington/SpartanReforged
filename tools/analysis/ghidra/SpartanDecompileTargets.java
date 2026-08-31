// Decompile a small explicit address set and record its immediate call context.
// @category SpartanReforged

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;

import java.io.File;
import java.io.PrintWriter;
import java.util.LinkedHashMap;
import java.util.Map;

public class SpartanDecompileTargets extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 2) throw new IllegalArgumentException("output directory plus addresses required");
        File output = new File(args[0]);
        output.mkdirs();
        Map<Address, Function> targets = new LinkedHashMap<>();
        for (int i = 1; i < args.length; i++) {
            Address address = toAddr(args[i]);
            Function function = currentProgram.getFunctionManager().getFunctionContaining(address);
            if (function == null) function = currentProgram.getFunctionManager().getFunctionAt(address);
            if (function == null) {
                println("No function for " + address);
                continue;
            }
            targets.put(function.getEntryPoint(), function);
        }

        DecompInterface decompiler = new DecompInterface();
        decompiler.toggleCCode(true);
        decompiler.toggleSyntaxTree(true);
        if (!decompiler.openProgram(currentProgram)) throw new IllegalStateException("decompiler open failed");
        try (PrintWriter index = new PrintWriter(new File(output, "index.tsv"), "UTF-8")) {
            index.println("entry\tname\tbodyMin\tbodyMax\tcallerCount\tcalleeCount\tdecompileCompleted");
            for (Function function : targets.values()) {
                DecompileResults result = decompiler.decompileFunction(function, 120, monitor);
                int callers = 0;
                ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(function.getEntryPoint());
                while (refs.hasNext()) { refs.next(); callers++; }
                int callees = function.getCalledFunctions(monitor).size();
                index.println(function.getEntryPoint() + "\t" + function.getName() + "\t" + function.getBody().getMinAddress() +
                    "\t" + function.getBody().getMaxAddress() + "\t" + callers + "\t" + callees + "\t" + result.decompileCompleted());
                try (PrintWriter out = new PrintWriter(new File(output, function.getEntryPoint() + ".c"), "UTF-8")) {
                    out.println("/* entry=" + function.getEntryPoint() + " name=" + function.getName() + " */");
                    if (result.decompileCompleted()) out.println(result.getDecompiledFunction().getC());
                    else out.println("/* " + result.getErrorMessage() + " */");
                }
                try (PrintWriter out = new PrintWriter(new File(output, function.getEntryPoint() + "_calls.tsv"), "UTF-8")) {
                    out.println("kind\tentry\tname");
                    refs = currentProgram.getReferenceManager().getReferencesTo(function.getEntryPoint());
                    while (refs.hasNext()) {
                        Reference ref = refs.next();
                        Function caller = currentProgram.getFunctionManager().getFunctionContaining(ref.getFromAddress());
                        if (caller != null) out.println("caller\t" + caller.getEntryPoint() + "\t" + caller.getName());
                    }
                    for (Function callee : function.getCalledFunctions(monitor)) {
                        out.println("callee\t" + callee.getEntryPoint() + "\t" + callee.getName());
                    }
                }
            }
        } finally {
            decompiler.dispose();
        }
    }
}
