
import sys
import types
import inspect

def isstring(s):
    # if we use Python 3
    if (sys.version_info[0] >= 3):
        return isinstance(s, str)
    # we use Python 2
    return isinstance(s, basestring)


def normalize_func(func):
    # return None for builtins
    return None if (inspect.isbuiltin(func)) else func

def get_doc(func):
  doc = inspect.getdoc(func)
  if doc is None:
    func = normalize_func(func)
    if func is None:
      return None
    else:
      doc = inspect.getdoc(func)
  return doc
  

def get_property_doc(target, prop):
    return next(
        (
            inspect.getdoc(obj.fget)
            for name, obj in inspect.getmembers(
                type(target), inspect.isdatadescriptor
            )
            if (isinstance(obj, property) and name == prop)
        ),
        None,
    )

def get_argspec(func):
  try:
    if sys.version_info[0] >= 3:
      return inspect.getfullargspec(func)
    else:
      return inspect.getargspec(func)
  except TypeError:
    return None

def get_arguments(func):
    func = normalize_func(func)
    if func is None:
      return None
    argspec = get_argspec(func)
    if argspec is None:
      return None
    args = argspec.args
    if 'self' in args:
      args.remove('self')
    return args

def get_r_representation(default):
    if callable(default) and hasattr(default, '__name__'):
        arg_value = default.__name__
    elif default is None:
        arg_value = "NULL"
    elif type(default) == type(True):
        arg_value = "TRUE" if default == True else "FALSE"
    elif isstring(default):
      arg_value = "\"%s\"" % default
    elif isinstance(default, int):
      arg_value = "%rL" % default
    elif isinstance(default, float):
      arg_value = "%r" % default
    elif isinstance(default, list):
        arg_value = "c("
        for i, item in enumerate(default):
            arg_value += (
                f"{get_r_representation(item)})"
                if i is (len(default) - 1)
                else f"{get_r_representation(item)}, "
            )

    elif isinstance(default, (tuple, set)):
        arg_value = "list("
        for i, item in enumerate(default):
            if i is (len(default) - 1):
                arg_value += f"{get_r_representation(item)})"
            else:
                arg_value += f"{get_r_representation(item)}, "
    elif isinstance(default, dict):
        arg_value = "list("
        for i in range(len(default)):
            i_arg_value = f"{default.keys()[i]} = {get_r_representation(default.values()[i])}"

            arg_value += (
                f"{i_arg_value})"
                if i is (len(default) - 1)
                else f"{i_arg_value}, "
            )

    else:
        arg_value = "%r" % default

    # if the value starts with "tf." then convert to $ usage
    if (arg_value.startswith("tf.")):
      arg_value = arg_value.replace(".", "$")

    return(arg_value)

def generate_signature_for_function(func):
    """Given a function, returns a string representing its args."""

    func = normalize_func(func)
    if func is None:
      return None

    args_list = []

    argspec = get_argspec(func)
    if argspec is None:
      return None

    first_arg_with_default = (
        len(argspec.args or []) - len(argspec.defaults or []))
    args_list.extend(
        arg for arg in argspec.args[:first_arg_with_default] if arg != "self"
    )

    if argspec.varargs == "args" and hasattr(argspec, 'keywords') and argspec.keywords == "kwds":
      original_func = func.__closure__[0].cell_contents
      return generate_signature_for_function(original_func)

    if argspec.defaults:
        for arg, default in zip(
          argspec.args[first_arg_with_default:], argspec.defaults):
            arg_value = get_r_representation(default)
            args_list.append(f"{arg} = {arg_value}")
    if argspec.varargs:
      args_list.append("...")
    if hasattr(argspec, 'keywords') and argspec.keywords:
      args_list.append("...")
    return "(" + ", ".join(args_list) + ")"

