// Report bounded references and bytes for candidate MODELS VU1 program regions.
// @category SpartanReforged

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;

import java.io.File;
import java.io.PrintWriter;

public class SpartanVu1ModelsTrace extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 2) {
            throw new IllegalArgumentException("output file plus one or more target addresses required");
        }
        File output = new File(args[0]);
        File parent = output.getParentFile();
        if (parent != null) parent.mkdirs();
        Memory memory = currentProgram.getMemory();
        try (PrintWriter out = new PrintWriter(output, "UTF-8")) {
            out.println("kind\ttarget\tfrom\tfunctionEntry\tfunctionName\tbytes");
            for (int i = 1; i < args.length; i++) {
                String[] spec = args[i].split(":", 2);
                Address target = toAddr(spec[0]);
                long length = spec.length == 2 ? Long.decode(spec[1]) : 1;
                if (length < 1 || length > 0x10000) throw new IllegalArgumentException("invalid range length");
                byte[] sample = new byte[32];
                int read = 0;
                try {
                    read = memory.getBytes(target, sample);
                } catch (Exception ignored) {
                    // Uninitialized globals can still have useful code references.
                }
                StringBuilder hex = new StringBuilder();
                for (int j = 0; j < read; j++) hex.append(String.format("%02x", sample[j] & 0xff));
                out.println("target\t" + target + "\t\t\t\t" + hex);
                for (long offset = 0; offset < length; offset++) {
                    Address location = target.add(offset);
                    ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(location);
                    while (refs.hasNext()) {
                        Reference ref = refs.next();
                        Function function = currentProgram.getFunctionManager().getFunctionContaining(ref.getFromAddress());
                        out.println("reference\t" + location + "\t" + ref.getFromAddress() + "\t" +
                            (function == null ? "" : function.getEntryPoint()) + "\t" +
                            (function == null ? "" : function.getName()) + "\t");
                    }
                }
            }
        }
    }
}
