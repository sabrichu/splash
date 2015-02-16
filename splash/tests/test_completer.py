# -*- coding: utf-8 -*-
from __future__ import absolute_import
import functools

import pytest
lupa = pytest.importorskip("lupa")


def _complete(completer, code):
    """
    Ask completer to complete the ``code``;
    cursor position is specified by | symbol.
    """
    cursor_pos = code.index("|")
    code = code.replace("|", "")
    res = completer.complete(code, cursor_pos)
    assert res["status"] == "ok"
    assert res["cursor_end"] == cursor_pos
    return res["matches"]


@pytest.fixture()
def complete(completer):
    return functools.partial(_complete, completer)


def test_complete_keywords(complete):
    assert "function" in complete("fun|")
    assert "true" in  complete("while t| do")


def test_complete_keywords_after_space(complete):
    assert [] == complete("fun |")


def test_dont_complete_keywords_as_attributes(complete):
    assert "function" not in complete("x.fun|")
    assert "function" not in complete("x:fun|")


def test_complete_globals(complete):
    res = complete("x = tab|")
    assert "table" in res

    res = complete("x = s|")
    assert "string" in res
    assert "select" in res
    assert "spoon" not in res
    assert all(m.startswith("s") for m in res)


def test_complete_user_globals(complete, configured_lua):
    configured_lua.execute("spoon = 5")
    res = complete("x = s|")
    assert "string" in res
    assert "select" in res
    assert "spoon" in res


def test_dont_complete_globals_as_attributes(complete):
    assert "string" not in complete("foo = x.s|")


def test_no_completions_on_nothing(complete):
    assert complete("|") == []
    assert complete(" | ") == []


def test_globals_attributes(complete):
    res = complete("foo = string.|")
    assert {'len', 'lower', 'reverse', 'upper'} <= set(res)
    assert 'concat' not in res

    assert complete("foo = string.l|") == ["len", "lower"]


def test_globals_attributes_index_notation(complete):
    res = complete("foo = string['|")
    assert {"len']", "lower']", "reverse']", "upper']"} <= set(res)
    assert "concat']" not in res

    res = complete('foo = string["|')
    assert {'len"]', 'lower"]', 'reverse"]', 'upper"]'} <= set(res)


def test_globals_attributes_index_notation_prefix(complete):
    assert complete('foo = string["l|') == ['len"]', 'lower"]']


def test_globals_without_dot(complete):
    assert complete("foo = string|") == []


def test_globals_without_dot_multiple(complete):
    assert complete("strings=""; foo = string|") == ["strings"]


def test_globals_attributes_nested_false_positive(complete):
    assert complete("foo = table.string.|") == []


def test_globals_attributes_nested(complete, configured_lua):
    configured_lua.execute("""
    weight = 20
    key = "foo"
    tbl={foo={width=10, heigth=5, nested={hello="world"}}}
    """)
    assert complete("tbl.foo.w|") == ["width"]
    assert complete("tbl['foo'].w|") == ["width"]
    assert complete('tbl["foo"].w|') == ["width"]
    assert complete('tbl.foo.nested.|') == ["hello"]
    assert complete('tbl["foo"].nested.|') == ["hello"]
    assert complete('tbl["foo"]["nested"].|') == ["hello"]
    assert complete('tbl[\'foo\']["nested"].|') == ["hello"]
    assert complete('tbl[\'foo"].w|') == []
    assert complete('tbl["foo\'].w|') == []
    assert complete('tbl.bar.w|') == []
    assert complete("tbl['bar'].w|") == []
    assert complete("tbl[key].w|") == []    # not supported


@pytest.mark.xfail(reason="not implemented")
def test_globals_attributes_dynamic_lookup(complete, configured_lua):
    configured_lua.execute("""
    key = "foo"
    tbl={foo={width=10, heigth=5}}
    """)
    assert complete("tbl[key].w|") == ["width"]    # not supported


def test_globals_attributes_nested_method(complete, configured_lua):
    configured_lua.execute("""
    obj = {foo="bar"}
    function obj:hello()
        return "hello"
    end
    tbl = {prop=obj}
    """)

    assert complete("tbl.prop.|") == ["foo", "hello"]
    assert complete("tbl.prop:|") == ["hello"]
    assert complete("tbl['prop'].|") == ["foo", "hello"]
    assert complete("tbl[\"prop\"]:|") == ["hello"]


def test_globals_attributes_nested_broken(complete, configured_lua):
    configured_lua.execute("""
    tbl = {prop={foo="bar"}}
    """)
    assert complete("tbl:prop.|") == []
    assert complete("tbl:prop:|") == []


def test_not_attributes(complete):
    assert complete("string..|") == []
    assert complete("(:|") == []


def test_complete_array(complete, configured_lua):
    configured_lua.execute("foo = {'x', 'y', z=5}")
    assert complete("foo.|") == ["z"]


def test_complete_methods(complete, configured_lua):
    configured_lua.execute("""
    tbl = {foo="bar"}
    function tbl:hello()
        return 123
    end
    """)
    assert complete("tbl:|") == ["hello"]     # fixme: metamethods?
    assert complete("tbl.|") == ["foo", "hello"]


def test_complete_function_result(complete, configured_lua):
    configured_lua.execute("""
    function foo()
        return {bar="baz"}
    end
    """)
    # It is too hard for a completer to return a proper result,
    # but at least there shouldn't be spurious matches.
    assert complete("foo().b|") == []


def test_complete_local_variables(complete):
    res = complete("""
    status = "statue"
    stats = "sterling"
    x = st|
    """)
    assert res == ["stats", "status", "string"]


def test_complete_local_variables_unicode(complete):
    res = complete(u"""
    привет = ""
    пр|
    """)
    assert res == []   # unicode identifiers are not allowed in Lua


def test_complete_latter_local_variables(complete):
    res = complete("""
    x = st|
    status = "statue"
    stats = "sterling"
    """)
    assert res == ["stats", "status", "string"]


def test_complete_string_metamethod(complete, configured_lua):
    configured_lua.execute("txt = 'hello'")
    assert "upper" in complete("txt:|")
    assert ["upper"] == complete("txt:up|")


@pytest.mark.xfail
def test_dont_complete_globals_inside_string(complete):
    assert "string" not in complete("x = 's|'")


def test_dont_complete_inside_identifier(complete):
    assert complete("loc|omotive") == []
