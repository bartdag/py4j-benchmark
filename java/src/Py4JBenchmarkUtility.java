import py4j.GatewayServer;

import java.util.Random;

public class Py4JBenchmarkUtility {

	public final int seed;
	private final Random random;

	public static final int DEFAULT_SEED = 17;

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

	public static int startCountdown(int count, Countdown pythonCountdown) {
		Countdown javaCountdown = new CountdownImpl();
		return pythonCountdown.countdown(count, javaCountdown);
	}

	public static byte[] echoBytes(byte[] bytes) {
		// Change first and last byte
		bytes[0] = 1;
		bytes[bytes.length - 1] = 2;
		return bytes;
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

	public static interface Echo {
		Object echo(Object param);
	}

	public static interface Countdown {
		int countdown(int count, Countdown countdownObject);
	}

	public static class CountdownImpl implements Countdown {
		@Override public int countdown(int count, Countdown countdownObject) {
			if (count == 0) {
				return 0;
			} else {
				return countdownObject.countdown(count - 1, this);
			}
		}
	}
}
