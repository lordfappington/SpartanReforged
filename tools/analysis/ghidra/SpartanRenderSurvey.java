// Bounded headless survey for Spartan: Total Warrior render-state research.
// @category SpartanReforged

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.data.DataType;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.scalar.Scalar;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;

import java.io.File;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

public class SpartanRenderSurvey extends GhidraScript {
    private static final List<String> TERMS = Arrays.asList(
        "material", "render", "texture", "alpha", "blend", "cloud", "flare", "glow",
        "zwrite", "depth", "transparen", "world", "environment", "models", ".mtl", "vu1"
    );

    private static final Set<Long> GS_REGISTERS = new HashSet<>(Arrays.asList(
        0x00L, 0x06L, 0x07L, 0x08L, 0x09L, 0x14L, 0x15L, 0x3bL,
        0x42L, 0x43L, 0x47L, 0x48L, 0x49L, 0x4aL, 0x4eL, 0x4fL
    ));

    private static String clean(String value) {
        return value.replace("\t", "\\t").replace("\r", "\\r").replace("\n", "\\n");
    }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            throw new IllegalArgumentException("expected one output directory argument");
        }
        File output = new File(args[0]);
        output.mkdirs();
        Listing listing = currentProgram.getListing();

        try (PrintWriter out = new PrintWriter(new File(output, "program.tsv"), "UTF-8")) {
            out.println("name\t" + currentProgram.getName());
            out.println("language\t" + currentProgram.getLanguageID());
            out.println("compiler\t" + currentProgram.getCompilerSpec().getCompilerSpecID());
            out.println("imageBase\t" + currentProgram.getImageBase());
            out.println("minAddress\t" + currentProgram.getMinAddress());
            out.println("maxAddress\t" + currentProgram.getMaxAddress());
            out.println("entry\t" + currentProgram.getSymbolTable().getExternalEntryPointIterator().next());
            out.println("functionCount\t" + currentProgram.getFunctionManager().getFunctionCount());
            for (MemoryBlock block : currentProgram.getMemory().getBlocks()) {
                out.println("block\t" + block.getName() + "\t" + block.getStart() + "\t" + block.getEnd() +
                    "\t" + block.getSize() + "\tR=" + block.isRead() + "\tW=" + block.isWrite() + "\tX=" + block.isExecute());
            }
        }

        try (PrintWriter out = new PrintWriter(new File(output, "keyword_strings.tsv"), "UTF-8")) {
            out.println("stringAddress\tstring\trefAddress\tfunctionEntry\tfunctionName");
            for (Data data : listing.getDefinedData(true)) {
                DataType type = data.getDataType();
                Object value = data.getValue();
                if (value == null || (!type.getName().toLowerCase(Locale.ROOT).contains("string") && !(value instanceof String))) {
                    continue;
                }
                String text = value.toString();
                String lower = text.toLowerCase(Locale.ROOT);
                boolean match = false;
                for (String term : TERMS) {
                    if (lower.contains(term)) {
                        match = true;
                        break;
                    }
                }
                if (!match) continue;
                ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(data.getAddress());
                boolean found = false;
                while (refs.hasNext()) {
                    found = true;
                    Reference ref = refs.next();
                    Function function = currentProgram.getFunctionManager().getFunctionContaining(ref.getFromAddress());
                    out.println(data.getAddress() + "\t" + clean(text) + "\t" + ref.getFromAddress() + "\t" +
                        (function == null ? "" : function.getEntryPoint()) + "\t" + (function == null ? "" : function.getName()));
                }
                if (!found) out.println(data.getAddress() + "\t" + clean(text) + "\t\t\t");
            }
        }

        try (PrintWriter out = new PrintWriter(new File(output, "gs_scalar_candidates.tsv"), "UTF-8")) {
            out.println("instruction\tfunctionEntry\tfunctionName\tmnemonic\toperand\tvalueHex\tvalueDec");
            for (Instruction instruction : listing.getInstructions(true)) {
                for (int op = 0; op < instruction.getNumOperands(); op++) {
                    for (Object object : instruction.getOpObjects(op)) {
                        if (!(object instanceof Scalar)) continue;
                        Scalar scalar = (Scalar)object;
                        long value = scalar.getUnsignedValue();
                        if (!GS_REGISTERS.contains(value)) continue;
                        Function function = currentProgram.getFunctionManager().getFunctionContaining(instruction.getAddress());
                        out.println(instruction.getAddress() + "\t" + (function == null ? "" : function.getEntryPoint()) + "\t" +
                            (function == null ? "" : function.getName()) + "\t" + instruction.getMnemonicString() + "\t" + op +
                            "\t0x" + Long.toHexString(value) + "\t" + value);
                    }
                }
            }
        }
    }
}
