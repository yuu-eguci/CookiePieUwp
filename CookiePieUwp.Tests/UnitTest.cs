using CookiePieUwp.Helpers;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace CookiePieUwp.Tests
{
    [TestClass]
    public class UtilTests
    {
        [TestMethod]
        [DataRow(1, 2)]
        [DataRow(0, 1)]
        [DataRow(-1, 0)]
        public void AddOne_ReturnsNextInteger(int n, int expected)
        {
            Assert.AreEqual(expected, Util.AddOne(n));
        }

#if EXPECTED_FAILURE_TEST
        // Kept from the original CI experiment: this test must fail.
        // Compiled only with /p:IncludeExpectedFailureTest=true (see README).
        [TestMethod]
        public void AddOne_IntentionalFailure()
        {
            Assert.AreEqual(3, Util.AddOne(1), "Intentional failure to prove CI reports failing tests.");
        }
#endif
    }
}
