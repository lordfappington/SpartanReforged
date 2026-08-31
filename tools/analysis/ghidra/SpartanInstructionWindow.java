// Export a bounded instruction window for reproducible address-level research.
// @category SpartanReforged

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.Listing;

import java.io.File;
import java.io.PrintWriter;

public class SpartanInstructionWindow extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 3) {
            throw new IllegalArgumentException("output file, start address, and byte length required");
        }
        File output = new File(args[0]);
        File parent = output.getParentFile();
        if (parent != null) parent.mkdirs();
        Address start = toAddr(args[1]);
        long byteLength = Long.decode(args[2]);
        if (byteLength <= 0 || byteLength > 0x10000) {
            throw new IllegalArgumentException("byte length must be in 1..0x10000");
        }
        Address end = start.add(byteLength - 1);
        Listing listing = currentProgram.getListing();
        try (PrintWriter out = new PrintWriter(output, "UTF-8")) {
            out.println("address\tbytes\tmnemonic\toperands");
            Instruction instruction = listing.getInstructionAt(start);
            if (instruction == null) instruction = listing.getInstructionAfter(start);
            while (instruction != null && instruction.getAddress().compareTo(end) <= 0) {
                byte[] bytes = instruction.getBytes();
                StringBuilder hex = new StringBuilder();
                for (byte value : bytes) hex.append(String.format("%02x", value & 0xff));
                String text = instruction.toString();
                String mnemonic = instruction.getMnemonicString();
                String operands = text.length() > mnemonic.length()
                    ? text.substring(mnemonic.length()).trim()
                    : "";
                out.println(instruction.getAddress() + "\t" + hex + "\t" + mnemonic + "\t" + operands);
                instruction = instruction.getNext();
            }
        }
    }
}
