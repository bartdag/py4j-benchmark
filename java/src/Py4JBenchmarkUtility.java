import java.util.Random;

public class Py4JBenchmarkUtility {

	private final int seed;
	private final Random random;

	public Py4JBenchmarkUtility(int seed) {
		this.seed = seed;
		random = new Random(seed);
	}

	public byte[] getBytes(int length) {
		byte[] bytes = new byte[length];
		random.nextBytes(bytes);
		return bytes;
	}
}
