import unittest
import sqlite3
import finalproject as fp

try:
    conn=sqlite3.connect('finalproject.db')
except:
    print('failed to open.')
    sys.exit(1)
cur=conn.cursor()

class TestYelp(unittest.TestCase):
    def testYelpRequest(self):
        yelp_data = fp.getYelpData("breakfast", "Ann Arbor")
        self.assertTrue(type(yelp_data) == list)
        self.assertTrue(len(yelp_data) > 5)
        self.assertTrue(type(yelp_data[0]) == fp.Yelp)
        self.assertTrue("Ann Arbor" in yelp_data[0].address)
    def testYelpCache(self):
        cache_data = fp.loadCache()
        self.assertTrue(type(cache_data) == dict)
        self.assertTrue("https://api.yelp.com/v3/businesses/searchlimit-50_location-Ann Arbor_offset-0_radius-16000_sort_by-distance_term-breakfast" in cache_data)

class TestDataBase(unittest.TestCase):
    def testBizs(self):
        fp.init_db()
        cur.execute("SELECT * FROM businesses")
        inital_results = cur.fetchall()
        self.assertFalse(inital_results)
        yelp_data = fp.getYelpData("breakfast", "Ann Arbor")
        fp.loadYelpData(yelp_data)
        cur.execute("SELECT * FROM businesses")
        results = cur.fetchall()
        self.assertTrue(type(results) == list)
        self.assertTrue(len(results) >= 100)
        self.assertTrue(len(results[0]) == 5)
    def testReviews(self):
        fp.init_db()
        cur.execute("SELECT * FROM reviews")
        inital_results = cur.fetchall()
        self.assertFalse(inital_results)
        yelp_data = fp.getYelpData("breakfast", "Ann Arbor")
        fp.loadYelpData(yelp_data)
        cur.execute("SELECT * FROM reviews")
        results = cur.fetchall()
        self.assertTrue(type(results) == list)
        self.assertTrue(len(results) >= 100)
        self.assertTrue(len(results[0]) == 5)

class TestProcessing(unittest.TestCase):
    def testHighestRated(self):
        fp.init_db()
        yelp_data = fp.getYelpData("breakfast", "Ann Arbor")
        fp.loadYelpData(yelp_data)
        results = fp.getHighestRated()
        self.assertEqual(len(results), 5)
        for res in results:
            self.assertTrue(res[1] > 3.0)
    def testLowestRated(self):
        fp.init_db()
        yelp_data = fp.getYelpData("breakfast", "Ann Arbor")
        fp.loadYelpData(yelp_data)
        results = fp.getLowestRated()
        self.assertEqual(len(results), 5)
        for res in results:
            self.assertTrue(res[1] <= 3.0)

    def testHighestPrice(self):
        fp.init_db()
        yelp_data = fp.getYelpData("breakfast", "Ann Arbor")
        fp.loadYelpData(yelp_data)
        results = fp.getHighPrice()
        self.assertEqual(len(results), 5)
        for res in results:
            self.assertTrue(len(res[4]) > 2)
            self.assertTrue(len(res[4]) != 0)

    def testLowestPrice(self):
        fp.init_db()
        yelp_data = fp.getYelpData("breakfast", "Ann Arbor")
        fp.loadYelpData(yelp_data)
        results = fp.getLowestPrice()
        self.assertEqual(len(results), 5)
        for res in results:
            self.assertTrue(len(res[4]) <= 2)
            self.assertTrue(len(res[4]) != 0)


unittest.main()
