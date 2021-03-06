import re
import types

import actions
import jstypes
from validator.compat import (FX10_DEFINITION, FX13_DEFINITION,
                              FX30_DEFINITION)
from validator.constants import BUGZILLA_BUG, EVENT_ASSIGNMENT


JS_URL = re.compile("href=[\'\"]javascript:")


def set_innerHTML(new_value, traverser):
    """Tests that values being assigned to innerHTML are not dangerous."""
    return _set_HTML_property("innerHTML", new_value, traverser)


def set_outerHTML(new_value, traverser):
    """Tests that values being assigned to outerHTML are not dangerous."""
    return _set_HTML_property("outerHTML", new_value, traverser)


# TODO(valcom): Make this generic and put it in utils
def _set_HTML_property(function, new_value, traverser):
    if not isinstance(new_value, jstypes.JSWrapper):
        new_value = jstypes.JSWrapper(new_value, traverser=traverser)

    if new_value.is_literal():
        literal_value = new_value.get_literal_value()
        if isinstance(literal_value, types.StringTypes):
            # Static string assignments

            # Test for on* attributes and script tags.
            if EVENT_ASSIGNMENT.search(literal_value.lower()):
                traverser.warning(
                    err_id=("testcases_javascript_instancetypes",
                            "set_%s" % function, "event_assignment"),
                    warning="Event handler assignment via %s" % function,
                    description=("When assigning event handlers, %s "
                                 "should never be used. Rather, use a "
                                 "proper technique, like addEventListener."
                                 % function,
                                 "Event handler code: %s"
                                 % literal_value.encode("ascii", "replace")),
                    signing_severity="medium")
            elif ("<script" in literal_value or
                  JS_URL.search(literal_value)):
                traverser.err.warning(
                    err_id=("testcases_javascript_instancetypes",
                            "set_%s" % function, "script_assignment"),
                    warning="Scripts should not be created with `%s`"
                            % function,
                    description="`%s` should not be used to add scripts to "
                                "pages via script tags or JavaScript URLs. "
                                "Instead, use event listeners and external "
                                "JavaScript." % function,
                    signing_severity="medium")
            else:
                # Everything checks out, but we still want to pass it through
                # the markup validator. Turn off strict mode so we don't get
                # warnings about malformed HTML.
                from validator.testcases.markup.markuptester import \
                                                                MarkupParser
                parser = MarkupParser(traverser.err, strict=False, debug=True)
                parser.process(traverser.filename, literal_value, "xul")

    else:
        # Variable assignments
        traverser.err.warning(
            err_id=("testcases_javascript_instancetypes", "set_%s" % function,
                    "variable_assignment"),
            warning="Markup should not be passed to `%s` dynamically."
                    % function,
            description="Due to both security and performance concerns, "
                        "%s may not be set using dynamic values which have "
                        "not been adequately sanitized. This can lead to "
                        "security issues or fairly serious performance "
                        "degradation." % function,
            filename=traverser.filename,
            line=traverser.line,
            column=traverser.position,
            context=traverser.context)


def set_on_event(new_value, traverser):
    """Ensure that on* properties are not assigned string values."""

    is_literal = new_value.is_literal()

    if (is_literal and
            isinstance(new_value.get_literal_value(), types.StringTypes)):
        traverser.warning(
            err_id=("testcases_javascript_instancetypes", "set_on_event",
                    "on*_str_assignment"),
            warning="on* property being assigned string",
            description="Event handlers in JavaScript should not be "
                        "assigned by setting an on* property to a "
                        "string of JS code. Rather, consider using "
                        "addEventListener.",
            signing_severity="medium")
    elif (not is_literal and isinstance(new_value.value, jstypes.JSObject) and
          "handleEvent" in new_value.value.data):
        traverser.warning(
            err_id=("js", "on*", "handleEvent"),
            warning="`handleEvent` no longer implemented in Gecko 18.",
            description="As of Gecko 18, objects with `handleEvent` methods "
                        "may no longer be assigned to `on*` properties. Doing "
                        "so will be equivalent to assigning `null` to the "
                        "property.")


def get_isElementContentWhitespace(traverser):
    traverser.err.error(
        err_id=("testcases_javascript_instanceproperties", "get_iECW"),
        error="isElementContentWhitespace property removed in Gecko 10.",
        description='The "isElementContentWhitespace" property has been '
                    'removed. See %s for more information.'
                    % BUGZILLA_BUG % 687422,
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context,
        for_appversions=FX10_DEFINITION,
        compatibility_type="error",
        tier=5)


def startendMarker(*args):
    traverser = args[0] if len(args) == 1 else args[1]
    traverser.err.notice(
        err_id=("testcases_javascript_instanceproperties",
                "get_startendMarker"),
        notice="`_startMarker` and `_endMarker` changed in Gecko 13",
        description="The `_startMarker` and `_endMarker` variables have "
                    "changed in a backward-incompatible way in Gecko 13. They "
                    "are now element references instead of numeric indices. "
                    "See %s for more information." % BUGZILLA_BUG % 731563,
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context,
        for_appversions=FX13_DEFINITION,
        compatibility_type="error",
        tier=5)


def _get_xml(name):
    """Handle all of the xml* compatibility problems introduced in Gecko 10."""
    bugs = {"xmlEncoding": 687426,
            "xmlStandalone": 693154,
            "xmlVersion": 693162}

    def wrapper(traverser):
        traverser.err.error(
            err_id=("testcases_javascript_instanceproperties", "_get_xml",
                    name),
            error="%s has been removed in Gecko 10" % name,
            description='The "%s" property has been removed. See %s for more '
                        'information.' % (name, BUGZILLA_BUG % bugs[name]),
            filename=traverser.filename,
            line=traverser.line,
            column=traverser.position,
            context=traverser.context,
            for_appversions=FX10_DEFINITION,
            compatibility_type="error",
            tier=5)
    return {"get": wrapper}


def set__proto__(new_value, traverser):
    traverser.warning(
        err_id=("testcases_javascript_instanceproperties", "__proto__"),
        warning="Using __proto__ or setPrototypeOf to set a prototype is now "
                "deprecated.",
        description="Use of __proto__ or setPrototypeOf to set a prototype "
                    "causes severe performance degredation, and is "
                    "deprecated. You should use Object.create instead. "
                    "See bug %s for more information." % BUGZILLA_BUG % 948227)


def set__exposedProps__(new_value, traverser):
    traverser.warning(
        err_id=("testcases_javascript_instanceproperties", "__exposedProps__"),
        warning="Use of deprecated __exposedProps__ declaration",
        description=(
            "The use of __exposedProps__ to expose objects to unprivileged "
            "scopes is dangerous, and has been deprecated. If objects "
            "must be exposed to unprivileged scopes, `cloneInto` or "
            "`exportFunction` should be used instead."),
        signing_severity="high")


def get_DOM_VK_ENTER(traverser):
    traverser.warning(
        err_id=("testcases_javascript_instanceproperties", "__proto__"),
        warning="DOM_VK_ENTER has been removed.",
        description="DOM_VK_ENTER has been removed. Removing it from your "
                    "code shouldn't have any impact since it was never "
                    "triggered in Firefox anyway. See bug %s for more "
                    "information." % BUGZILLA_BUG % 969247,
        for_appversions=FX30_DEFINITION,
        compatibility_type="warning",
        tier=5)


def set_contentScript(value, traverser):
    """Warns when values are assigned to the `contentScript` properties,
    which are essentially the same as calling `eval`."""

    if value.is_literal():
        content_script = actions._get_as_str(value)

        # Avoid import loop.
        from validator.testcases.scripting import test_js_file
        test_js_file(
            traverser.err, traverser.filename, content_script,
            line=traverser.line, context=traverser.context)
    else:
        traverser.warning(
            err_id=("testcases_javascript_instanceproperties",
                    "contentScript", "set_non_literal"),
            warning="`contentScript` properties should not be used",
            description="Creating content scripts from dynamic values "
                        "is dangerous and error-prone. Please use a separate "
                        "JavaScript file, along with the "
                        "`contentScriptFile` property instead.",
            signing_severity="high")


OBJECT_DEFINITIONS = {
    "_endMarker": {"get": startendMarker,
                   "set": startendMarker},
    "_startMarker": {"get": startendMarker,
                     "set": startendMarker},
    "innerHTML": {"set": set_innerHTML},
    "outerHTML": {"set": set_outerHTML},
    "contentScript": {"set": set_contentScript},
    "isElementContentWhitespace": {"get": get_isElementContentWhitespace},
    "xmlEncoding": _get_xml("xmlEncoding"),
    "xmlStandalone": _get_xml("xmlStandalone"),
    "xmlVersion": _get_xml("xmlVersion"),
    "__proto__": {"set": set__proto__},
    "__exposedProps__": {"set": set__exposedProps__},
    "DOM_VK_ENTER": {"get": get_DOM_VK_ENTER},
}


def get_operation(mode, prop):
    """
    This returns the object definition function for a particular property
    or mode. mode should either be 'set' or 'get'.
    """

    if prop in OBJECT_DEFINITIONS and mode in OBJECT_DEFINITIONS[prop]:
        return OBJECT_DEFINITIONS[prop][mode]

    elif mode == "set" and unicode(prop).startswith("on"):
        # We can't match all of them manually, so grab all the "on*" properties
        # and funnel them through the set_on_event function.

        return set_on_event
