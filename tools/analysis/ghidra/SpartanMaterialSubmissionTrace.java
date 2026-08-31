// Locate bounded runtime-material and submission-queue field references.
// @category SpartanReforged

import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.scalar.Scalar;

import java.io.File;
import java.io.PrintWriter;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

public class SpartanMaterialSubmissionTrace extends GhidraScript {
    private static final Set<Long> OFFSETS = new HashSet<>(Arrays.asList(
        0x30L, 0x40L, 0x50L, 0x60L, 0x70L, 0x80L, 0x90L,
        0x420L, 0x424L, 0x428L, 0x42cL, 0x430L,
        0x11570L, 0x115d0L, 0x115f0L,
        0x115fcL, 0x115fdL, 0x115feL, 0x11600L, 0x11604L,
        0x14L, 0x15L, 0x17L, 0x4aL, 0x50L,
        0x1400L, 0x1500L, 0x1700L, 0x4a00L, 0x5000L,
        0x14000000L, 0x15000000L, 0x17000000L, 0x4a000000L, 0x50000000L
    ));

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) throw new IllegalArgumentException("expected one output file");
        File output = new File(args[0]);
        File parent = output.getParentFile();
        if (parent != null) parent.mkdirs();
        try (PrintWriter out = new PrintWriter(output, "UTF-8")) {
            out.println("address\tfunctionEntry\tfunctionName\toffset\tinstruction");
            for (Instruction instruction : currentProgram.getListing().getInstructions(true)) {
                Set<Long> emitted = new HashSet<>();
                for (int operand = 0; operand < instruction.getNumOperands(); operand++) {
                    for (Object object : instruction.getOpObjects(operand)) {
                        if (!(object instanceof Scalar)) continue;
                        long value = ((Scalar)object).getUnsignedValue();
                        if (!OFFSETS.contains(value) || !emitted.add(value)) continue;
                        Function function = currentProgram.getFunctionManager().getFunctionContaining(instruction.getAddress());
                        out.println(instruction.getAddress() + "\t" +
                            (function == null ? "" : function.getEntryPoint()) + "\t" +
                            (function == null ? "" : function.getName()) + "\t0x" +
                            Long.toHexString(value) + "\t" + instruction);
                    }
                }
            }
        }
    }
}
