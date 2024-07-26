import unittest

from pythonosc.dispatcher import Dispatcher, Handler


class TestDispatcher(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.dispatcher = Dispatcher()

    def sortAndAssertSequenceEqual(self, expected, result):
        def sort(lst):
            return sorted(lst, key=lambda x: x.callback)

        return self.assertSequenceEqual(sort(expected), sort(result))

    def test_empty_by_default(self):
        self.sortAndAssertSequenceEqual(
            [], self.dispatcher.handlers_for_address("/test")
        )

    def test_use_default_handler_when_set_and_no_match(self):
        handler = object()
        self.dispatcher.set_default_handler(handler)

        self.sortAndAssertSequenceEqual(
            [Handler(handler, [])], self.dispatcher.handlers_for_address("/test")
        )

    def test_simple_map_and_match(self):
        handler = object()
        self.dispatcher.map("/test", handler, 1, 2, 3)
        self.dispatcher.map("/test2", handler)
        self.sortAndAssertSequenceEqual(
            [Handler(handler, [1, 2, 3])], self.dispatcher.handlers_for_address("/test")
        )
        self.sortAndAssertSequenceEqual(
            [Handler(handler, [])], self.dispatcher.handlers_for_address("/test2")
        )

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
            self.sortAndAssertSequenceEqual(
                [Handler(index, [])], self.dispatcher.handlers_for_address(address)
            )

        self.sortAndAssertSequenceEqual(
            [Handler(1, []), Handler(2, [])],
            self.dispatcher.handlers_for_address("/second/?"),
        )

        self.sortAndAssertSequenceEqual(
            [Handler(3, []), Handler(4, []), Handler(5, [])],
            self.dispatcher.handlers_for_address("/third/*"),
        )

    def test_do_not_match_over_slash(self):
        self.dispatcher.map("/foo/bar/1", 1)
        self.dispatcher.map("/foo/bar/2", 2)

        self.sortAndAssertSequenceEqual([], self.dispatcher.handlers_for_address("/*"))

    def test_match_middle_star(self):
        self.dispatcher.map("/foo/bar/1", 1)
        self.dispatcher.map("/foo/bar/2", 2)

        self.sortAndAssertSequenceEqual(
            [Handler(2, [])], self.dispatcher.handlers_for_address("/foo/*/2")
        )

    def test_match_multiple_stars(self):
        self.dispatcher.map("/foo/bar/1", 1)
        self.dispatcher.map("/foo/bar/2", 2)

        self.sortAndAssertSequenceEqual(
            [Handler(1, []), Handler(2, [])],
            self.dispatcher.handlers_for_address("/*/*/*"),
        )

    def test_match_address_contains_plus_as_character(self):
        self.dispatcher.map("/footest/bar+tender/1", 1)

        self.sortAndAssertSequenceEqual(
            [Handler(1, [])], self.dispatcher.handlers_for_address("/foo*/bar+*/*")
        )
        self.sortAndAssertSequenceEqual(
            [Handler(1, [])], self.dispatcher.handlers_for_address("/foo*/bar*/*")
        )

    def test_call_correct_dispatcher_on_star(self):
        self.dispatcher.map("/a+b", 1)
        self.dispatcher.map("/aaab", 2)
        self.sortAndAssertSequenceEqual(
            [Handler(2, [])], self.dispatcher.handlers_for_address("/aaab")
        )
        self.sortAndAssertSequenceEqual(
            [Handler(1, [])], self.dispatcher.handlers_for_address("/a+b")
        )

    def test_map_star(self):
        self.dispatcher.map("/starbase/*", 1)
        self.sortAndAssertSequenceEqual(
            [Handler(1, [])], self.dispatcher.handlers_for_address("/starbase/bar")
        )

    def test_map_root_star(self):
        self.dispatcher.map("/*", 1)
        self.sortAndAssertSequenceEqual(
            [Handler(1, [])], self.dispatcher.handlers_for_address("/anything/matches")
        )

    def test_map_double_stars(self):
        self.dispatcher.map("/foo/*/bar/*", 1)
        self.sortAndAssertSequenceEqual(
            [Handler(1, [])], self.dispatcher.handlers_for_address("/foo/wild/bar/wild")
        )
        self.sortAndAssertSequenceEqual(
            [], self.dispatcher.handlers_for_address("/foo/wild/nomatch/wild")
        )

    def test_multiple_handlers(self):
        self.dispatcher.map("/foo/bar", 1)
        self.dispatcher.map("/foo/bar", 2)
        self.sortAndAssertSequenceEqual(
            [Handler(1, []), Handler(2, [])],
            self.dispatcher.handlers_for_address("/foo/bar"),
        )

    def test_multiple_handlers_with_wildcard_map(self):
        self.dispatcher.map("/foo/bar", 1)
        self.dispatcher.map("/*", 2)
        self.sortAndAssertSequenceEqual(
            [Handler(1, []), Handler(2, [])],
            self.dispatcher.handlers_for_address("/foo/bar"),
        )

    def test_unmap(self):
        def dummyhandler():
            pass

        # Test with handler returned by map
        returnedhandler = self.dispatcher.map("/map/me", dummyhandler)
        self.sortAndAssertSequenceEqual(
            [Handler(dummyhandler, [])], self.dispatcher.handlers_for_address("/map/me")
        )
        self.dispatcher.unmap("/map/me", returnedhandler)
        self.sortAndAssertSequenceEqual(
            [], self.dispatcher.handlers_for_address("/map/me")
        )

        # Test with reconstructing handler
        self.dispatcher.map("/map/me/too", dummyhandler)
        self.sortAndAssertSequenceEqual(
            [Handler(dummyhandler, [])],
            self.dispatcher.handlers_for_address("/map/me/too"),
        )
        self.dispatcher.unmap("/map/me/too", dummyhandler)
        self.sortAndAssertSequenceEqual(
            [], self.dispatcher.handlers_for_address("/map/me/too")
        )

    def test_unmap_exception(self):
        def dummyhandler():
            pass

        with self.assertRaises(ValueError):
            self.dispatcher.unmap("/unmap/exception", dummyhandler)

        handlerobj = self.dispatcher.map("/unmap/somethingelse", dummyhandler())
        with self.assertRaises(ValueError):
            self.dispatcher.unmap("/unmap/exception", handlerobj)


if __name__ == "__main__":
    unittest.main()
