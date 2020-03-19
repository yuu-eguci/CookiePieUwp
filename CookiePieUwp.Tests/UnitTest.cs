
using System;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace CookiePieUwp.Tests
{
    [TestClass]
    public class UnitTest1
    {
        [TestMethod]
        public void TestMethod1()
        {
            Assert.AreEqual(2, CookiePieUwp.Helpers.Util.AddOne(1), "1 + 1 is 2!");
        }
    }
}
