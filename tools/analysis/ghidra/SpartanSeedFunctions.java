// Seed only explicitly reviewed missed functions in the ignored Ghidra project.
// @category SpartanReforged

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;

public class SpartanSeedFunctions extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length == 0) throw new IllegalArgumentException("function start addresses required");
        for (String arg : args) {
            Address start = toAddr(arg);
            disassemble(start);
            Function function = getFunctionAt(start);
            if (function == null) function = createFunction(start, "render_seed_" + start);
            println("Seeded " + function.getName() + " at " + function.getEntryPoint() + " through " + function.getBody().getMaxAddress());
        }
    }
}
