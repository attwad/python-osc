import unittest

import dispatcher

class TestDispatcher(unittest.TestCase):
  
  def setUp(self):
    super().setUp()
    self.dispatcher = dispatcher.Dispatcher()

  def sortAndAssertSequenceEqual(self, expected, result):
    return self.assertSequenceEqual(sorted(expected), sorted(result))

  def test_empty_by_default(self):
    self.assertEqual([], self.dispatcher.handlers_for_address('/test'))

  def test_simple_map_and_match(self):
    handler = object()
    self.dispatcher.map('/test', handler)
    self.assertEqual(
        [handler], self.dispatcher.handlers_for_address('/test'))

  def test_example_from_spec(self):
    addresses = [
        "/first/this/one",
        "/second/1",
        "/second/2",
        "/third/a",
        "/third/b",
        "/third/c",
    ]
    for index, address in enumerate(addresses):
      self.dispatcher.map(address, index)

    for index, address in enumerate(addresses):
      self.assertListEqual(
          [index], self.dispatcher.handlers_for_address(address))

    self.sortAndAssertSequenceEqual(
      [1, 2], self.dispatcher.handlers_for_address("/second/?"))

    self.sortAndAssertSequenceEqual(
      [3, 4, 5], self.dispatcher.handlers_for_address("/third/*"))

  def test_do_not_match_over_slash(self):
    self.dispatcher.map('/foo/bar/1', 1)
    self.dispatcher.map('/foo/bar/2', 2)

    self.sortAndAssertSequenceEqual(
        [], self.dispatcher.handlers_for_address("/*"))

  def test_match_middle_star(self):
    self.dispatcher.map('/foo/bar/1', 1)
    self.dispatcher.map('/foo/bar/2', 2)

    self.sortAndAssertSequenceEqual(
        [2], self.dispatcher.handlers_for_address("/foo/*/2"))

if __name__ == "__main__":
  unittest.main()
