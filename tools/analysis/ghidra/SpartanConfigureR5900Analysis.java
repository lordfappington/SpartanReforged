// Apply the extension-recommended bounded analysis settings before auto-analysis.
// @category SpartanReforged

import ghidra.app.script.GhidraScript;

public class SpartanConfigureR5900Analysis extends GhidraScript {
    @Override
    public void run() throws Exception {
        setAnalysisOption(currentProgram, "Decompiler Parameter ID", "false");
        println("Decompiler Parameter ID disabled for R5900 analysis");
    }
}
