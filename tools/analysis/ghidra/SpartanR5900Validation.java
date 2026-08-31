// Record bounded examples of R5900-only instruction families after analysis.
// @category SpartanReforged

import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Instruction;

import java.io.File;
import java.io.PrintWriter;
import java.util.Locale;
import java.util.Map;
import java.util.TreeMap;

public class SpartanR5900Validation extends GhidraScript {
    private static String family(String mnemonic) {
        String value = mnemonic.toLowerCase(Locale.ROOT);
        if (value.equals("lq")) return "LQ";
        if (value.equals("sq")) return "SQ";
        if ((value.startsWith("p") && !value.equals("pref")) || value.equals("qfsrv") ||
            ((value.startsWith("madd") || value.startsWith("msub")) && !value.contains("."))) {
            return "MMI";
        }
        if (value.equals("lqc2") || value.equals("sqc2") || value.equals("qmfc2") || value.equals("qmtc2") ||
            value.equals("cfc2") || value.equals("ctc2") || value.startsWith("vcallms") || value.startsWith("v")) {
            return "COP2_VU";
        }
        return null;
    }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) throw new IllegalArgumentException("expected one output file");
        File output = new File(args[0]);
        File parent = output.getParentFile();
        if (parent != null) parent.mkdirs();
        Map<String, Integer> counts = new TreeMap<>();
        Map<String, Integer> examples = new TreeMap<>();
        try (PrintWriter out = new PrintWriter(output, "UTF-8")) {
            out.println("family\taddress\tbytes\tmnemonic\toperands");
            for (Instruction instruction : currentProgram.getListing().getInstructions(true)) {
                String group = family(instruction.getMnemonicString());
                if (group == null) continue;
                counts.put(group, counts.getOrDefault(group, 0) + 1);
                int emitted = examples.getOrDefault(group, 0);
                if (emitted >= 32) continue;
                byte[] bytes = instruction.getBytes();
                StringBuilder hex = new StringBuilder();
                for (byte value : bytes) hex.append(String.format("%02x", value & 0xff));
                String text = instruction.toString();
                String mnemonic = instruction.getMnemonicString();
                String operands = text.length() > mnemonic.length() ? text.substring(mnemonic.length()).trim() : "";
                out.println(group + "\t" + instruction.getAddress() + "\t" + hex + "\t" + mnemonic + "\t" + operands);
                examples.put(group, emitted + 1);
            }
            for (Map.Entry<String, Integer> entry : counts.entrySet()) {
                out.println("COUNT\t" + entry.getKey() + "\t" + entry.getValue() + "\t\t");
            }
        }
    }
}
