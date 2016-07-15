import py4j.GatewayServer;

import java.util.Random;

public class Py4JBenchmarkUtility {

	private final int seed;
	private final Random random;

	private static final int DEFAULT_SEED = 17;

	public Py4JBenchmarkUtility(int seed) {
		this.seed = seed;
		random = new Random(seed);
	}

	public byte[] getBytes(int length) {
		byte[] bytes = new byte[length];
		random.nextBytes(bytes);
		return bytes;
	}

	public Object callEcho(Echo echo, Object param) {
		return echo.echo(param);
	}

	public static void main(String[] args) {
		int seed = DEFAULT_SEED;
		if (args.length > 0) {
			seed = Integer.parseInt(args[0]);
		}
		Py4JBenchmarkUtility utility = new Py4JBenchmarkUtility(seed);
		GatewayServer server = new GatewayServer(utility);
		server.start(true);
	}

	public interface Echo {
		Object echo(Object param);
	}
}
