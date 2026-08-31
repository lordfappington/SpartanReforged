// Locate aligned VIF MPG command candidates outside decoded EE instructions.
// @category SpartanReforged

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.mem.Memory;

import java.io.File;
import java.io.PrintWriter;

public class SpartanVu1MpgSurvey extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 3) throw new IllegalArgumentException("output, start, end required");
        File output = new File(args[0]);
        File parent = output.getParentFile();
        if (parent != null) parent.mkdirs();
        Address start = toAddr(args[1]);
        Address end = toAddr(args[2]);
        Memory memory = currentProgram.getMemory();
        try (PrintWriter out = new PrintWriter(output, "UTF-8")) {
            out.println("address\traw\tnum\tdestination\tpreceding12");
            for (Address address = start; address.compareTo(end) <= 0; address = address.add(4)) {
                if (!memory.contains(address) || currentProgram.getListing().getInstructionContaining(address) != null) continue;
                int raw;
                try { raw = memory.getInt(address); } catch (Exception ignored) { continue; }
                if (((raw >>> 24) & 0x7f) != 0x4a) continue;
                int num = (raw >>> 16) & 0xff;
                int destination = raw & 0x7ff;
                if (num == 0) num = 256;
                if (num > 256) continue;
                StringBuilder prefix = new StringBuilder();
                try {
                    byte[] bytes = new byte[12];
                    memory.getBytes(address.subtract(12), bytes);
                    for (byte value : bytes) prefix.append(String.format("%02x", value & 0xff));
                } catch (Exception ignored) { }
                out.printf("%s\t%08x\t%d\t0x%03x\t%s%n", address, raw, num, destination, prefix);
            }
        }
    }
}
