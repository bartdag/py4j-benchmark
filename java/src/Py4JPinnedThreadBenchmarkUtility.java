import py4j.ClientServer;

public class Py4JPinnedThreadBenchmarkUtility {

	public static void main(String[] args) {
		int seed = Py4JBenchmarkUtility.DEFAULT_SEED;
		if (args.length > 0) {
			seed = Integer.parseInt(args[0]);
		}
		Py4JBenchmarkUtility utility = new Py4JBenchmarkUtility(seed);
		ClientServer clientServer = new ClientServer(utility);
		// Necessary for earlier versions of Py4J
		clientServer.startServer(true);
	}
}
