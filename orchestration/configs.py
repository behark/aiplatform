import collections
import typing
from dataclasses import dataclass
__all__ = ['Config']

@dataclass(init=False, eq=False, slots=True, kw_only=True, match_args=False)
class Config:
    """The base class for NetworkX configuration.

    There are two ways to use this to create configurations. The recommended way
    is to subclass ``Config`` with docs and annotations.

    >>> class MyConfig(Config):
    ...     '''Breakfast!'''
    ...
    ...     eggs: int
    ...     spam: int
    ...
    ...     def _on_setattr(self, key, value):
    ...         assert isinstance(value, int) and value >= 0
    ...         return value
    >>> cfg = MyConfig(eggs=1, spam=5)

    Another way is to simply pass the initial configuration as keyword arguments to
    the ``Config`` instance:

    >>> cfg1 = Config(eggs=1, spam=5)
    >>> cfg1
    Config(eggs=1, spam=5)

    Once defined, config items may be modified, but can't be added or deleted by default.
    ``Config`` is a ``Mapping``, and can get and set configs via attributes or brackets:

    >>> cfg.eggs = 2
    >>> cfg.eggs
    2
    >>> cfg["spam"] = 42
    >>> cfg["spam"]
    42

    For convenience, it can also set configs within a context with the "with" statement:

    >>> with cfg(spam=3):
    ...     print("spam (in context):", cfg.spam)
    spam (in context): 3
    >>> print("spam (after context):", cfg.spam)
    spam (after context): 42

    Subclasses may also define ``_on_setattr`` (as done in the example above)
    to ensure the value being assigned is valid:

    >>> cfg.spam = -1
    Traceback (most recent call last):
        ...
    AssertionError

    If a more flexible configuration object is needed that allows adding and deleting
    configurations, then pass ``strict=False`` when defining the subclass:

    >>> class FlexibleConfig(Config, strict=False):
    ...     default_greeting: str = "Hello"
    >>> flexcfg = FlexibleConfig()
    >>> flexcfg.name = "Mr. Anderson"
    >>> flexcfg
    FlexibleConfig(default_greeting='Hello', name='Mr. Anderson')
    """

    def __init_subclass__(cls, strict=True):
        cls._strict = strict

    def __new__(cls, **kwargs):
        orig_class = cls
        if cls is Config:
            cls = type(cls.__name__, (cls,), {'__annotations__': dict.fromkeys(kwargs, typing.Any)})
        cls = dataclass(eq=False, repr=cls._strict, slots=cls._strict, kw_only=True, match_args=False)(cls)
        if not cls._strict:
            cls.__repr__ = _flexible_repr
        cls._orig_class = orig_class
        cls._prev = None
        cls._context_stack = []
        instance = object.__new__(cls)
        instance.__init__(**kwargs)
        return instance

    def _on_setattr(self, key, value):
        """Process config value and check whether it is valid. Useful for subclasses."""
        return value

    def _on_delattr(self, key):
        """Callback for when a config item is being deleted. Useful for subclasses."""

    def __dir__(self):
        return self.__dataclass_fields__.keys()

    def __setattr__(self, key, value):
        if self._strict and key not in self.__dataclass_fields__:
            raise AttributeError(f'Invalid config name: {key!r}')
        value = self._on_setattr(key, value)
        object.__setattr__(self, key, value)
        self.__class__._prev = None

    def __delattr__(self, key):
        if self._strict:
            raise TypeError(f"Configuration items can't be deleted (can't delete {key!r}).")
        self._on_delattr(key)
        object.__delattr__(self, key)
        self.__class__._prev = None

    def __contains__(self, key):
        return key in self.__dataclass_fields__ if self._strict else key in self.__dict__

    def __iter__(self):
        return iter(self.__dataclass_fields__ if self._strict else self.__dict__)

    def __len__(self):
        return len(self.__dataclass_fields__ if self._strict else self.__dict__)

    def __reversed__(self):
        return reversed(self.__dataclass_fields__ if self._strict else self.__dict__)

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError as err:
            raise KeyError(*err.args) from None

    def __setitem__(self, key, value):
        try:
            self.__setattr__(key, value)
        except AttributeError as err:
            raise KeyError(*err.args) from None

    def __delitem__(self, key):
        try:
            self.__delattr__(key)
        except AttributeError as err:
            raise KeyError(*err.args) from None
    _ipython_key_completions_ = __dir__

    def get(self, key, default=None):
        return getattr(self, key, default)

    def items(self):
        return collections.abc.ItemsView(self)

    def keys(self):
        return collections.abc.KeysView(self)

    def values(self):
        return collections.abc.ValuesView(self)

    def __eq__(self, other):
        if not isinstance(other, Config):
            return NotImplemented
        return self._orig_class == other._orig_class and self.items() == other.items()

    def __reduce__(self):
        return (self._deserialize, (self._orig_class, dict(self)))

    @staticmethod
    def _deserialize(cls, kwargs):
        return cls(**kwargs)

    def __call__(self, **kwargs):
        kwargs = {key: self._on_setattr(key, val) for key, val in kwargs.items()}
        prev = dict(self)
        for key, val in kwargs.items():
            setattr(self, key, val)
        self.__class__._prev = prev
        return self

    def __enter__(self):
        if self.__class__._prev is None:
            raise RuntimeError('Config being used as a context manager without config items being set. Set config items via keyword arguments when calling the config object. For example, using config as a context manager should be like:\n\n    >>> with cfg(breakfast="spam"):\n    ...     ...  # Do stuff\n')
        self.__class__._context_stack.append(self.__class__._prev)
        self.__class__._prev = None
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        prev = self.__class__._context_stack.pop()
        for key, val in prev.items():
            setattr(self, key, val)

def _flexible_repr(self):
    return f'{self.__class__.__qualname__}(' + ', '.join((f'{key}={val!r}' for key, val in self.__dict__.items())) + ')'
collections.abc.Mapping.register(Config)

class BackendPriorities(Config, strict=False):
    """Configuration to control automatic conversion to and calling of backends.

    Priority is given to backends listed earlier.

    Parameters
    ----------
    algos : list of backend names
        This controls "algorithms" such as ``nx.pagerank`` that don't return a graph.
    generators : list of backend names
        This controls "generators" such as ``nx.from_pandas_edgelist`` that return a graph.
    kwargs : variadic keyword arguments of function name to list of backend names
        This allows each function to be configured separately and will override the config
        in ``algos`` or ``generators`` if present. The dispatchable function name may be
        gotten from the ``.name`` attribute such as ``nx.pagerank.name`` (it's typically
        the same as the name of the function).
    """
    algos: list[str]
    generators: list[str]

    def _on_setattr(self, key, value):
        from .backends import _registered_algorithms, backend_info
        if key in {'algos', 'generators'}:
            pass
        elif key not in _registered_algorithms:
            raise AttributeError(f"Invalid config name: {key!r}. Expected 'algos', 'generators', or a name of a dispatchable function (e.g. `.name` attribute of the function).")
        if not (isinstance(value, list) and all((isinstance(x, str) for x in value))):
            raise TypeError(f'{key!r} config must be a list of backend names; got {value!r}')
        if (missing := {x for x in value if x not in backend_info}):
            missing = ', '.join(map(repr, sorted(missing)))
            raise ValueError(f'Unknown backend when setting {key!r}: {missing}')
        return value

    def _on_delattr(self, key):
        if key in {'algos', 'generators'}:
            raise TypeError(f"{key!r} configuration item can't be deleted.")

class NetworkXConfig(Config):
    """Configuration for NetworkX that controls behaviors such as how to use backends.

    Attribute and bracket notation are supported for getting and setting configurations::

        >>> nx.config.backend_priority == nx.config["backend_priority"]
        True

    Parameters
    ----------
    backend_priority : list of backend names or dict or BackendPriorities
        Enable automatic conversion of graphs to backend graphs for functions
        implemented by the backend. Priority is given to backends listed earlier.
        This is a nested configuration with keys ``algos``, ``generators``, and,
        optionally, function names. Setting this value to a list of backend names
        will set ``nx.config.backend_priority.algos``. For more information, see
        ``help(nx.config.backend_priority)``. Default is empty list.

    backends : Config mapping of backend names to backend Config
        The keys of the Config mapping are names of all installed NetworkX backends,
        and the values are their configurations as Config mappings.

    cache_converted_graphs : bool
        If True, then save converted graphs to the cache of the input graph. Graph
        conversion may occur when automatically using a backend from `backend_priority`
        or when using the `backend=` keyword argument to a function call. Caching can
        improve performance by avoiding repeated conversions, but it uses more memory.
        Care should be taken to not manually mutate a graph that has cached graphs; for
        example, ``G[u][v][k] = val`` changes the graph, but does not clear the cache.
        Using methods such as ``G.add_edge(u, v, weight=val)`` will clear the cache to
        keep it consistent. ``G.__networkx_cache__.clear()`` manually clears the cache.
        Default is True.

    fallback_to_nx : bool
        If True, then "fall back" and run with the default "networkx" implementation
        for dispatchable functions not implemented by backends of input graphs. When a
        backend graph is passed to a dispatchable function, the default behavior is to
        use the implementation from that backend if possible and raise if not. Enabling
        ``fallback_to_nx`` makes the networkx implementation the fallback to use instead
        of raising, and will convert the backend graph to a networkx-compatible graph.
        Default is False.

    warnings_to_ignore : set of strings
        Control which warnings from NetworkX are not emitted. Valid elements:

        - `"cache"`: when a cached value is used from ``G.__networkx_cache__``.

    Notes
    -----
    Environment variables may be used to control some default configurations:

    - ``NETWORKX_BACKEND_PRIORITY``: set ``backend_priority.algos`` from comma-separated names.
    - ``NETWORKX_CACHE_CONVERTED_GRAPHS``: set ``cache_converted_graphs`` to True if nonempty.
    - ``NETWORKX_FALLBACK_TO_NX``: set ``fallback_to_nx`` to True if nonempty.
    - ``NETWORKX_WARNINGS_TO_IGNORE``: set `warnings_to_ignore` from comma-separated names.

    and can be used for finer control of ``backend_priority`` such as:

    - ``NETWORKX_BACKEND_PRIORITY_ALGOS``: same as ``NETWORKX_BACKEND_PRIORITY``
      to set ``backend_priority.algos``.

    This is a global configuration. Use with caution when using from multiple threads.
    """
    backend_priority: BackendPriorities
    backends: Config
    cache_converted_graphs: bool
    fallback_to_nx: bool
    warnings_to_ignore: set[str]

    def _on_setattr(self, key, value):
        from .backends import backend_info
        if key == 'backend_priority':
            if isinstance(value, list):
                value = BackendPriorities(**dict(self.backend_priority, algos=self.backend_priority._on_setattr('algos', value)))
            elif isinstance(value, dict):
                kwargs = value
                value = BackendPriorities(algos=[], generators=[])
                for key, val in kwargs.items():
                    setattr(value, key, val)
            elif not isinstance(value, BackendPriorities):
                raise TypeError(f'{key!r} config must be a dict of lists of backend names; got {value!r}')
        elif key == 'backends':
            if not (isinstance(value, Config) and all((isinstance(key, str) for key in value)) and all((isinstance(val, Config) for val in value.values()))):
                raise TypeError(f'{key!r} config must be a Config of backend configs; got {value!r}')
            if (missing := {x for x in value if x not in backend_info}):
                missing = ', '.join(map(repr, sorted(missing)))
                raise ValueError(f'Unknown backend when setting {key!r}: {missing}')
        elif key in {'cache_converted_graphs', 'fallback_to_nx'}:
            if not isinstance(value, bool):
                raise TypeError(f'{key!r} config must be True or False; got {value!r}')
        elif key == 'warnings_to_ignore':
            if not (isinstance(value, set) and all((isinstance(x, str) for x in value))):
                raise TypeError(f'{key!r} config must be a set of warning names; got {value!r}')
            known_warnings = {'cache'}
            if (missing := {x for x in value if x not in known_warnings}):
                missing = ', '.join(map(repr, sorted(missing)))
                raise ValueError(f'Unknown warning when setting {key!r}: {missing}. Valid entries: ' + ', '.join(sorted(known_warnings)))
        return value
from ..api import APIClient
from .resource import Collection, Model

class ConfigCollection(Collection):
    """Configs on the Docker server."""
    model = Config

    def create(self, **kwargs):
        obj = self.client.api.create_config(**kwargs)
        obj.setdefault('Spec', {})['Name'] = kwargs.get('name')
        return self.prepare_model(obj)
    create.__doc__ = APIClient.create_config.__doc__

    def get(self, config_id):
        """
        Get a config.

        Args:
            config_id (str): Config ID.

        Returns:
            (:py:class:`Config`): The config.

        Raises:
            :py:class:`docker.errors.NotFound`
                If the config does not exist.
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        return self.prepare_model(self.client.api.inspect_config(config_id))

    def list(self, **kwargs):
        """
        List configs. Similar to the ``docker config ls`` command.

        Args:
            filters (dict): Server-side list filtering options.

        Returns:
            (list of :py:class:`Config`): The configs.

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        resp = self.client.api.configs(**kwargs)
        return [self.prepare_model(obj) for obj in resp]
'\n    pygments.lexers.configs\n    ~~~~~~~~~~~~~~~~~~~~~~~\n\n    Lexers for configuration file formats.\n\n    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.\n    :license: BSD, see LICENSE for details.\n'
import re
from pygments.lexer import ExtendedRegexLexer, RegexLexer, default, words, bygroups, include, using, line_re
from pygments.token import Text, Comment, Operator, Keyword, Name, String, Number, Punctuation, Whitespace, Literal, Error, Generic
from pygments.lexers.shell import BashLexer
from pygments.lexers.data import JsonLexer
__all__ = ['IniLexer', 'SystemdLexer', 'DesktopLexer', 'RegeditLexer', 'PropertiesLexer', 'KconfigLexer', 'Cfengine3Lexer', 'ApacheConfLexer', 'SquidConfLexer', 'NginxConfLexer', 'LighttpdConfLexer', 'DockerLexer', 'TerraformLexer', 'TermcapLexer', 'TerminfoLexer', 'PkgConfigLexer', 'PacmanConfLexer', 'AugeasLexer', 'TOMLLexer', 'NestedTextLexer', 'SingularityLexer', 'UnixConfigLexer']

class IniLexer(RegexLexer):
    """
    Lexer for configuration files in INI style.
    """
    name = 'INI'
    aliases = ['ini', 'cfg', 'dosini']
    filenames = ['*.ini', '*.cfg', '*.inf', '.editorconfig']
    mimetypes = ['text/x-ini', 'text/inf']
    url = 'https://en.wikipedia.org/wiki/INI_file'
    version_added = ''
    tokens = {'root': [('\\s+', Whitespace), ('[;#].*', Comment.Single), ('(\\[.*?\\])([ \\t]*)$', bygroups(Keyword, Whitespace)), ('(.*?)([ \\t]*)([=:])([ \\t]*)(["\'])', bygroups(Name.Attribute, Whitespace, Operator, Whitespace, String), 'quoted_value'), ('(.*?)([ \\t]*)([=:])([ \\t]*)([^;#\\n]*)(\\\\)(\\s+)', bygroups(Name.Attribute, Whitespace, Operator, Whitespace, String, Text, Whitespace), 'value'), ('(.*?)([ \\t]*)([=:])([ \\t]*)([^ ;#\\n]*(?: +[^ ;#\\n]+)*)', bygroups(Name.Attribute, Whitespace, Operator, Whitespace, String)), ('(.+?)$', Name.Attribute)], 'quoted_value': [('([^"\'\\n]*)(["\'])(\\s*)', bygroups(String, String, Whitespace), '#pop'), ('[;#].*', Comment.Single), ('$', String, '#pop')], 'value': [('\\s+', Whitespace), ('(\\s*)(.*)(\\\\)([ \\t]*)', bygroups(Whitespace, String, Text, Whitespace)), ('.*$', String, '#pop')]}

    def analyse_text(text):
        npos = text.find('\n')
        if npos < 3:
            return False
        if text[0] == '[' and text[npos - 1] == ']':
            return 0.8
        return False

class DesktopLexer(RegexLexer):
    """
    Lexer for .desktop files.
    """
    name = 'Desktop file'
    url = 'https://specifications.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html'
    aliases = ['desktop']
    filenames = ['*.desktop']
    mimetypes = ['application/x-desktop']
    version_added = '2.16'
    tokens = {'root': [('^[ \\t]*\\n', Whitespace), ('^(#.*)(\\n)', bygroups(Comment.Single, Whitespace)), ('(\\[[^\\]\\n]+\\])(\\n)', bygroups(Keyword, Whitespace)), ('([-A-Za-z0-9]+)(\\[[^\\] \\t=]+\\])?([ \\t]*)(=)([ \\t]*)([^\\n]*)([ \\t\\n]*\\n)', bygroups(Name.Attribute, Name.Namespace, Whitespace, Operator, Whitespace, String, Whitespace))]}

    def analyse_text(text):
        if text.startswith('[Desktop Entry]'):
            return 1.0
        if re.search('^\\[Desktop Entry\\][ \\t]*$', text[:500], re.MULTILINE) is not None:
            return 0.9
        return 0.0

class SystemdLexer(RegexLexer):
    """
    Lexer for systemd unit files.
    """
    name = 'Systemd'
    url = 'https://www.freedesktop.org/software/systemd/man/systemd.syntax.html'
    aliases = ['systemd']
    filenames = ['*.service', '*.socket', '*.device', '*.mount', '*.automount', '*.swap', '*.target', '*.path', '*.timer', '*.slice', '*.scope']
    version_added = '2.16'
    tokens = {'root': [('^[ \\t]*\\n', Whitespace), ('^([;#].*)(\\n)', bygroups(Comment.Single, Whitespace)), ('(\\[[^\\]\\n]+\\])(\\n)', bygroups(Keyword, Whitespace)), ('([^=]+)([ \\t]*)(=)([ \\t]*)([^\\n]*)(\\\\)(\\n)', bygroups(Name.Attribute, Whitespace, Operator, Whitespace, String, Text, Whitespace), 'value'), ('([^=]+)([ \\t]*)(=)([ \\t]*)([^\\n]*)(\\n)', bygroups(Name.Attribute, Whitespace, Operator, Whitespace, String, Whitespace))], 'value': [('^([;#].*)(\\n)', bygroups(Comment.Single, Whitespace)), ('([ \\t]*)([^\\n]*)(\\\\)(\\n)', bygroups(Whitespace, String, Text, Whitespace)), ('([ \\t]*)([^\\n]*)(\\n)', bygroups(Whitespace, String, Whitespace), '#pop')]}

    def analyse_text(text):
        if text.startswith('[Unit]'):
            return 1.0
        if re.search('^\\[Unit\\][ \\t]*$', text[:500], re.MULTILINE) is not None:
            return 0.9
        return 0.0

class RegeditLexer(RegexLexer):
    """
    Lexer for Windows Registry files produced by regedit.
    """
    name = 'reg'
    url = 'http://en.wikipedia.org/wiki/Windows_Registry#.REG_files'
    aliases = ['registry']
    filenames = ['*.reg']
    mimetypes = ['text/x-windows-registry']
    version_added = '1.6'
    tokens = {'root': [('Windows Registry Editor.*', Text), ('\\s+', Whitespace), ('[;#].*', Comment.Single), ('(\\[)(-?)(HKEY_[A-Z_]+)(.*?\\])$', bygroups(Keyword, Operator, Name.Builtin, Keyword)), ('("(?:\\\\"|\\\\\\\\|[^"])+")([ \\t]*)(=)([ \\t]*)', bygroups(Name.Attribute, Whitespace, Operator, Whitespace), 'value'), ('(.*?)([ \\t]*)(=)([ \\t]*)', bygroups(Name.Attribute, Whitespace, Operator, Whitespace), 'value')], 'value': [('-', Operator, '#pop'), ('(dword|hex(?:\\([0-9a-fA-F]\\))?)(:)([0-9a-fA-F,]+)', bygroups(Name.Variable, Punctuation, Number), '#pop'), ('.+', String, '#pop'), default('#pop')]}

    def analyse_text(text):
        return text.startswith('Windows Registry Editor')

class PropertiesLexer(RegexLexer):
    """
    Lexer for configuration files in Java's properties format.

    Note: trailing whitespace counts as part of the value as per spec
    """
    name = 'Properties'
    aliases = ['properties', 'jproperties']
    filenames = ['*.properties']
    mimetypes = ['text/x-java-properties']
    url = 'https://en.wikipedia.org/wiki/.properties'
    version_added = '1.4'
    tokens = {'root': [('[!#].*|/{2}.*', Comment.Single), ('\\n', Whitespace), ('^[^\\S\\n]+', Whitespace), default('key')], 'key': [('[^\\\\:=\\s]+', Name.Attribute), include('escapes'), ('([^\\S\\n]*)([:=])([^\\S\\n]*)', bygroups(Whitespace, Operator, Whitespace), ('#pop', 'value')), ('[^\\S\\n]+', Whitespace, ('#pop', 'value')), ('\\n', Whitespace, '#pop')], 'value': [('[^\\\\\\n]+', String), include('escapes'), ('\\n', Whitespace, '#pop')], 'escapes': [('(\\\\\\n)([^\\S\\n]*)', bygroups(String.Escape, Whitespace)), ('\\\\(.|\\n)', String.Escape)]}

def _rx_indent(level):
    tab_width = 8
    if tab_width == 2:
        space_repeat = '+'
    else:
        space_repeat = '{1,%d}' % (tab_width - 1)
    if level == 1:
        level_repeat = ''
    else:
        level_repeat = f'{{{level}}}'
    return f'(?:\\t| {space_repeat}\\t| {{{tab_width}}}){level_repeat}.*\\n'

class KconfigLexer(RegexLexer):
    """
    For Linux-style Kconfig files.
    """
    name = 'Kconfig'
    aliases = ['kconfig', 'menuconfig', 'linux-config', 'kernel-config']
    version_added = '1.6'
    filenames = ['Kconfig*', '*Config.in*', 'external.in*', 'standard-modules.in']
    mimetypes = ['text/x-kconfig']
    url = 'https://www.kernel.org/doc/html/latest/kbuild/kconfig-language.html'
    flags = 0

    def call_indent(level):
        return (_rx_indent(level), String.Doc, f'indent{level}')

    def do_indent(level):
        return [(_rx_indent(level), String.Doc), ('\\s*\\n', Text), default('#pop:2')]
    tokens = {'root': [('\\s+', Whitespace), ('#.*?\\n', Comment.Single), (words(('mainmenu', 'config', 'menuconfig', 'choice', 'endchoice', 'comment', 'menu', 'endmenu', 'visible if', 'if', 'endif', 'source', 'prompt', 'select', 'depends on', 'default', 'range', 'option'), suffix='\\b'), Keyword), ('(---help---|help)[\\t ]*\\n', Keyword, 'help'), ('(bool|tristate|string|hex|int|defconfig_list|modules|env)\\b', Name.Builtin), ('[!=&|]', Operator), ('[()]', Punctuation), ('[0-9]+', Number.Integer), ("'(''|[^'])*'", String.Single), ('"(""|[^"])*"', String.Double), ('\\S+', Text)], 'help': [('\\s*\\n', Text), call_indent(7), call_indent(6), call_indent(5), call_indent(4), call_indent(3), call_indent(2), call_indent(1), default('#pop')], 'indent7': do_indent(7), 'indent6': do_indent(6), 'indent5': do_indent(5), 'indent4': do_indent(4), 'indent3': do_indent(3), 'indent2': do_indent(2), 'indent1': do_indent(1)}

class Cfengine3Lexer(RegexLexer):
    """
    Lexer for CFEngine3 policy files.
    """
    name = 'CFEngine3'
    url = 'http://cfengine.org'
    aliases = ['cfengine3', 'cf3']
    filenames = ['*.cf']
    mimetypes = []
    version_added = '1.5'
    tokens = {'root': [('#.*?\\n', Comment), ('(body)(\\s+)(\\S+)(\\s+)(control)', bygroups(Keyword, Whitespace, Keyword, Whitespace, Keyword)), ('(body|bundle)(\\s+)(\\S+)(\\s+)(\\w+)(\\()', bygroups(Keyword, Whitespace, Keyword, Whitespace, Name.Function, Punctuation), 'arglist'), ('(body|bundle)(\\s+)(\\S+)(\\s+)(\\w+)', bygroups(Keyword, Whitespace, Keyword, Whitespace, Name.Function)), ('(")([^"]+)(")(\\s+)(string|slist|int|real)(\\s*)(=>)(\\s*)', bygroups(Punctuation, Name.Variable, Punctuation, Whitespace, Keyword.Type, Whitespace, Operator, Whitespace)), ('(\\S+)(\\s*)(=>)(\\s*)', bygroups(Keyword.Reserved, Whitespace, Operator, Text)), ('"', String, 'string'), ('(\\w+)(\\()', bygroups(Name.Function, Punctuation)), ('([\\w.!&|()]+)(::)', bygroups(Name.Class, Punctuation)), ('(\\w+)(:)', bygroups(Keyword.Declaration, Punctuation)), ('@[{(][^)}]+[})]', Name.Variable), ('[(){},;]', Punctuation), ('=>', Operator), ('->', Operator), ('\\d+\\.\\d+', Number.Float), ('\\d+', Number.Integer), ('\\w+', Name.Function), ('\\s+', Whitespace)], 'string': [('\\$[{(]', String.Interpol, 'interpol'), ('\\\\.', String.Escape), ('"', String, '#pop'), ('\\n', String), ('.', String)], 'interpol': [('\\$[{(]', String.Interpol, '#push'), ('[})]', String.Interpol, '#pop'), ('[^${()}]+', String.Interpol)], 'arglist': [('\\)', Punctuation, '#pop'), (',', Punctuation), ('\\w+', Name.Variable), ('\\s+', Whitespace)]}

class ApacheConfLexer(RegexLexer):
    """
    Lexer for configuration files following the Apache config file
    format.
    """
    name = 'ApacheConf'
    aliases = ['apacheconf', 'aconf', 'apache']
    filenames = ['.htaccess', 'apache.conf', 'apache2.conf']
    mimetypes = ['text/x-apacheconf']
    url = 'https://httpd.apache.org/docs/current/configuring.html'
    version_added = '0.6'
    flags = re.MULTILINE | re.IGNORECASE
    tokens = {'root': [('\\s+', Whitespace), ('#(.*\\\\\\n)+.*$|(#.*?)$', Comment), ('(<[^\\s>/][^\\s>]*)(?:(\\s+)(.*))?(>)', bygroups(Name.Tag, Whitespace, String, Name.Tag)), ('(</[^\\s>]+)(>)', bygroups(Name.Tag, Name.Tag)), ('[a-z]\\w*', Name.Builtin, 'value'), ('\\.+', Text)], 'value': [('\\\\\\n', Text), ('\\n+', Whitespace, '#pop'), ('\\\\', Text), ('[^\\S\\n]+', Whitespace), ('\\d+\\.\\d+\\.\\d+\\.\\d+(?:/\\d+)?', Number), ('\\d+', Number), ('/([*a-z0-9][*\\w./-]+)', String.Other), ('(on|off|none|any|all|double|email|dns|min|minimal|os|productonly|full|emerg|alert|crit|error|warn|notice|info|debug|registry|script|inetd|standalone|user|group)\\b', Keyword), ('"([^"\\\\]*(?:\\\\(.|\\n)[^"\\\\]*)*)"', String.Double), ('[^\\s"\\\\]+', Text)]}

class SquidConfLexer(RegexLexer):
    """
    Lexer for squid configuration files.
    """
    name = 'SquidConf'
    url = 'http://www.squid-cache.org/'
    aliases = ['squidconf', 'squid.conf', 'squid']
    filenames = ['squid.conf']
    mimetypes = ['text/x-squidconf']
    version_added = '0.9'
    flags = re.IGNORECASE
    keywords = ('access_log', 'acl', 'always_direct', 'announce_host', 'announce_period', 'announce_port', 'announce_to', 'anonymize_headers', 'append_domain', 'as_whois_server', 'auth_param_basic', 'authenticate_children', 'authenticate_program', 'authenticate_ttl', 'broken_posts', 'buffered_logs', 'cache_access_log', 'cache_announce', 'cache_dir', 'cache_dns_program', 'cache_effective_group', 'cache_effective_user', 'cache_host', 'cache_host_acl', 'cache_host_domain', 'cache_log', 'cache_mem', 'cache_mem_high', 'cache_mem_low', 'cache_mgr', 'cachemgr_passwd', 'cache_peer', 'cache_peer_access', 'cache_replacement_policy', 'cache_stoplist', 'cache_stoplist_pattern', 'cache_store_log', 'cache_swap', 'cache_swap_high', 'cache_swap_log', 'cache_swap_low', 'client_db', 'client_lifetime', 'client_netmask', 'connect_timeout', 'coredump_dir', 'dead_peer_timeout', 'debug_options', 'delay_access', 'delay_class', 'delay_initial_bucket_level', 'delay_parameters', 'delay_pools', 'deny_info', 'dns_children', 'dns_defnames', 'dns_nameservers', 'dns_testnames', 'emulate_httpd_log', 'err_html_text', 'fake_user_agent', 'firewall_ip', 'forwarded_for', 'forward_snmpd_port', 'fqdncache_size', 'ftpget_options', 'ftpget_program', 'ftp_list_width', 'ftp_passive', 'ftp_user', 'half_closed_clients', 'header_access', 'header_replace', 'hierarchy_stoplist', 'high_response_time_warning', 'high_page_fault_warning', 'hosts_file', 'htcp_port', 'http_access', 'http_anonymizer', 'httpd_accel', 'httpd_accel_host', 'httpd_accel_port', 'httpd_accel_uses_host_header', 'httpd_accel_with_proxy', 'http_port', 'http_reply_access', 'icp_access', 'icp_hit_stale', 'icp_port', 'icp_query_timeout', 'ident_lookup', 'ident_lookup_access', 'ident_timeout', 'incoming_http_average', 'incoming_icp_average', 'inside_firewall', 'ipcache_high', 'ipcache_low', 'ipcache_size', 'local_domain', 'local_ip', 'logfile_rotate', 'log_fqdn', 'log_icp_queries', 'log_mime_hdrs', 'maximum_object_size', 'maximum_single_addr_tries', 'mcast_groups', 'mcast_icp_query_timeout', 'mcast_miss_addr', 'mcast_miss_encode_key', 'mcast_miss_port', 'memory_pools', 'memory_pools_limit', 'memory_replacement_policy', 'mime_table', 'min_http_poll_cnt', 'min_icp_poll_cnt', 'minimum_direct_hops', 'minimum_object_size', 'minimum_retry_timeout', 'miss_access', 'negative_dns_ttl', 'negative_ttl', 'neighbor_timeout', 'neighbor_type_domain', 'netdb_high', 'netdb_low', 'netdb_ping_period', 'netdb_ping_rate', 'never_direct', 'no_cache', 'passthrough_proxy', 'pconn_timeout', 'pid_filename', 'pinger_program', 'positive_dns_ttl', 'prefer_direct', 'proxy_auth', 'proxy_auth_realm', 'query_icmp', 'quick_abort', 'quick_abort_max', 'quick_abort_min', 'quick_abort_pct', 'range_offset_limit', 'read_timeout', 'redirect_children', 'redirect_program', 'redirect_rewrites_host_header', 'reference_age', 'refresh_pattern', 'reload_into_ims', 'request_body_max_size', 'request_size', 'request_timeout', 'shutdown_lifetime', 'single_parent_bypass', 'siteselect_timeout', 'snmp_access', 'snmp_incoming_address', 'snmp_port', 'source_ping', 'ssl_proxy', 'store_avg_object_size', 'store_objects_per_bucket', 'strip_query_terms', 'swap_level1_dirs', 'swap_level2_dirs', 'tcp_incoming_address', 'tcp_outgoing_address', 'tcp_recv_bufsize', 'test_reachability', 'udp_hit_obj', 'udp_hit_obj_size', 'udp_incoming_address', 'udp_outgoing_address', 'unique_hostname', 'unlinkd_program', 'uri_whitespace', 'useragent_log', 'visible_hostname', 'wais_relay', 'wais_relay_host', 'wais_relay_port')
    opts = ('proxy-only', 'weight', 'ttl', 'no-query', 'default', 'round-robin', 'multicast-responder', 'on', 'off', 'all', 'deny', 'allow', 'via', 'parent', 'no-digest', 'heap', 'lru', 'realm', 'children', 'q1', 'q2', 'credentialsttl', 'none', 'disable', 'offline_toggle', 'diskd')
    actions = ('shutdown', 'info', 'parameter', 'server_list', 'client_list', 'squid.conf')
    actions_stats = ('objects', 'vm_objects', 'utilization', 'ipcache', 'fqdncache', 'dns', 'redirector', 'io', 'reply_headers', 'filedescriptors', 'netdb')
    actions_log = ('status', 'enable', 'disable', 'clear')
    acls = ('url_regex', 'urlpath_regex', 'referer_regex', 'port', 'proto', 'req_mime_type', 'rep_mime_type', 'method', 'browser', 'user', 'src', 'dst', 'time', 'dstdomain', 'ident', 'snmp_community')
    ipv4_group = '(\\d+|0x[0-9a-f]+)'
    ipv4 = f'({ipv4_group}(\\.{ipv4_group}){{3}})'
    ipv6_group = '([0-9a-f]{0,4})'
    ipv6 = f'({ipv6_group}(:{ipv6_group}){{1,7}})'
    bare_ip = f'({ipv4}|{ipv6})'
    ip = f'{bare_ip}(/({bare_ip}|\\d+))?'
    tokens = {'root': [('\\s+', Whitespace), ('#', Comment, 'comment'), (words(keywords, prefix='\\b', suffix='\\b'), Keyword), (words(opts, prefix='\\b', suffix='\\b'), Name.Constant), (words(actions, prefix='\\b', suffix='\\b'), String), (words(actions_stats, prefix='stats/', suffix='\\b'), String), (words(actions_log, prefix='log/', suffix='='), String), (words(acls, prefix='\\b', suffix='\\b'), Keyword), (ip, Number.Float), ('(?:\\b\\d+\\b(?:-\\b\\d+|%)?)', Number), ('\\S+', Text)], 'comment': [('\\s*TAG:.*', String.Escape, '#pop'), ('.+', Comment, '#pop'), default('#pop')]}

class NginxConfLexer(RegexLexer):
    """
    Lexer for Nginx configuration files.
    """
    name = 'Nginx configuration file'
    url = 'http://nginx.net/'
    aliases = ['nginx']
    filenames = ['nginx.conf']
    mimetypes = ['text/x-nginx-conf']
    version_added = '0.11'
    tokens = {'root': [('(include)(\\s+)([^\\s;]+)', bygroups(Keyword, Whitespace, Name)), ('[^\\s;#]+', Keyword, 'stmt'), include('base')], 'block': [('\\}', Punctuation, '#pop:2'), ('[^\\s;#]+', Keyword.Namespace, 'stmt'), include('base')], 'stmt': [('\\{', Punctuation, 'block'), (';', Punctuation, '#pop'), include('base')], 'base': [('#.*\\n', Comment.Single), ('on|off', Name.Constant), ('\\$[^\\s;#()]+', Name.Variable), ('([a-z0-9.-]+)(:)([0-9]+)', bygroups(Name, Punctuation, Number.Integer)), ('[a-z-]+/[a-z-+]+', String), ('[0-9]+[km]?\\b', Number.Integer), ('(~)(\\s*)([^\\s{]+)', bygroups(Punctuation, Whitespace, String.Regex)), ('[:=~]', Punctuation), ('[^\\s;#{}$]+', String), ('/[^\\s;#]*', Name), ('\\s+', Whitespace), ('[$;]', Text)]}

class LighttpdConfLexer(RegexLexer):
    """
    Lexer for Lighttpd configuration files.
    """
    name = 'Lighttpd configuration file'
    url = 'http://lighttpd.net/'
    aliases = ['lighttpd', 'lighty']
    filenames = ['lighttpd.conf']
    mimetypes = ['text/x-lighttpd-conf']
    version_added = '0.11'
    tokens = {'root': [('#.*\\n', Comment.Single), ('/\\S*', Name), ('[a-zA-Z._-]+', Keyword), ('\\d+\\.\\d+\\.\\d+\\.\\d+(?:/\\d+)?', Number), ('[0-9]+', Number), ('=>|=~|\\+=|==|=|\\+', Operator), ('\\$[A-Z]+', Name.Builtin), ('[(){}\\[\\],]', Punctuation), ('"([^"\\\\]*(?:\\\\.[^"\\\\]*)*)"', String.Double), ('\\s+', Whitespace)]}

class DockerLexer(RegexLexer):
    """
    Lexer for Docker configuration files.
    """
    name = 'Docker'
    url = 'http://docker.io'
    aliases = ['docker', 'dockerfile']
    filenames = ['Dockerfile', '*.docker']
    mimetypes = ['text/x-dockerfile-config']
    version_added = '2.0'
    _keywords = '(?:MAINTAINER|EXPOSE|WORKDIR|USER|STOPSIGNAL)'
    _bash_keywords = '(?:RUN|CMD|ENTRYPOINT|ENV|ARG|LABEL|ADD|COPY)'
    _lb = '(?:\\s*\\\\?\\s*)'
    flags = re.IGNORECASE | re.MULTILINE
    tokens = {'root': [('#.*', Comment), ('(FROM)([ \\t]*)(\\S*)([ \\t]*)(?:(AS)([ \\t]*)(\\S*))?', bygroups(Keyword, Whitespace, String, Whitespace, Keyword, Whitespace, String)), (f'(ONBUILD)(\\s+)({_lb})', bygroups(Keyword, Whitespace, using(BashLexer))), (f'(HEALTHCHECK)(\\s+)(({_lb}--\\w+=\\w+{_lb})*)', bygroups(Keyword, Whitespace, using(BashLexer))), (f'(VOLUME|ENTRYPOINT|CMD|SHELL)(\\s+)({_lb})(\\[.*?\\])', bygroups(Keyword, Whitespace, using(BashLexer), using(JsonLexer))), (f'(LABEL|ENV|ARG)(\\s+)(({_lb}\\w+=\\w+{_lb})*)', bygroups(Keyword, Whitespace, using(BashLexer))), (f'({_keywords}|VOLUME)\\b(\\s+)(.*)', bygroups(Keyword, Whitespace, String)), (f'({_bash_keywords})(\\s+)', bygroups(Keyword, Whitespace)), ('(.*\\\\\\n)*.+', using(BashLexer))]}

class TerraformLexer(ExtendedRegexLexer):
    """
    Lexer for terraformi ``.tf`` files.
    """
    name = 'Terraform'
    url = 'https://www.terraform.io/'
    aliases = ['terraform', 'tf', 'hcl']
    filenames = ['*.tf', '*.hcl']
    mimetypes = ['application/x-tf', 'application/x-terraform']
    version_added = '2.1'
    classes = ('backend', 'data', 'module', 'output', 'provider', 'provisioner', 'resource', 'variable')
    classes_re = '({})'.format('|'.join(classes))
    types = ('string', 'number', 'bool', 'list', 'tuple', 'map', 'set', 'object', 'null')
    numeric_functions = ('abs', 'ceil', 'floor', 'log', 'max', 'mix', 'parseint', 'pow', 'signum')
    string_functions = ('chomp', 'format', 'formatlist', 'indent', 'join', 'lower', 'regex', 'regexall', 'replace', 'split', 'strrev', 'substr', 'title', 'trim', 'trimprefix', 'trimsuffix', 'trimspace', 'upper')
    collection_functions = ('alltrue', 'anytrue', 'chunklist', 'coalesce', 'coalescelist', 'compact', 'concat', 'contains', 'distinct', 'element', 'flatten', 'index', 'keys', 'length', 'list', 'lookup', 'map', 'matchkeys', 'merge', 'range', 'reverse', 'setintersection', 'setproduct', 'setsubtract', 'setunion', 'slice', 'sort', 'sum', 'transpose', 'values', 'zipmap')
    encoding_functions = ('base64decode', 'base64encode', 'base64gzip', 'csvdecode', 'jsondecode', 'jsonencode', 'textdecodebase64', 'textencodebase64', 'urlencode', 'yamldecode', 'yamlencode')
    filesystem_functions = ('abspath', 'dirname', 'pathexpand', 'basename', 'file', 'fileexists', 'fileset', 'filebase64', 'templatefile')
    date_time_functions = ('formatdate', 'timeadd', 'timestamp')
    hash_crypto_functions = ('base64sha256', 'base64sha512', 'bcrypt', 'filebase64sha256', 'filebase64sha512', 'filemd5', 'filesha1', 'filesha256', 'filesha512', 'md5', 'rsadecrypt', 'sha1', 'sha256', 'sha512', 'uuid', 'uuidv5')
    ip_network_functions = ('cidrhost', 'cidrnetmask', 'cidrsubnet', 'cidrsubnets')
    type_conversion_functions = ('can', 'defaults', 'tobool', 'tolist', 'tomap', 'tonumber', 'toset', 'tostring', 'try')
    builtins = numeric_functions + string_functions + collection_functions + encoding_functions + filesystem_functions + date_time_functions + hash_crypto_functions + ip_network_functions + type_conversion_functions
    builtins_re = '({})'.format('|'.join(builtins))

    def heredoc_callback(self, match, ctx):
        start = match.start(1)
        yield (start, Operator, match.group(1))
        yield (match.start(2), String.Delimiter, match.group(2))
        ctx.pos = match.start(3)
        ctx.end = match.end(3)
        yield (ctx.pos, String.Heredoc, match.group(3))
        ctx.pos = match.end()
        hdname = match.group(2)
        tolerant = True
        lines = []
        for match in line_re.finditer(ctx.text, ctx.pos):
            if tolerant:
                check = match.group().strip()
            else:
                check = match.group().rstrip()
            if check == hdname:
                for amatch in lines:
                    yield (amatch.start(), String.Heredoc, amatch.group())
                yield (match.start(), String.Delimiter, match.group())
                ctx.pos = match.end()
                break
            else:
                lines.append(match)
        else:
            for amatch in lines:
                yield (amatch.start(), Error, amatch.group())
        ctx.end = len(ctx.text)
    tokens = {'root': [include('basic'), include('whitespace'), ('(".*")', bygroups(String.Double)), (words(('true', 'false'), prefix='\\b', suffix='\\b'), Name.Constant), (words(types, prefix='\\b', suffix='\\b'), Keyword.Type), include('identifier'), include('punctuation'), ('[0-9]+', Number)], 'basic': [('\\s*/\\*', Comment.Multiline, 'comment'), ('\\s*(#|//).*\\n', Comment.Single), include('whitespace'), ('(\\s*)([0-9a-zA-Z-_]+)(\\s*)(=?)(\\s*)(\\{)', bygroups(Whitespace, Name.Builtin, Whitespace, Operator, Whitespace, Punctuation)), ('(\\s*)([0-9a-zA-Z-_]+)(\\s*)(=)(\\s*)', bygroups(Whitespace, Name.Attribute, Whitespace, Operator, Whitespace)), ('(\\s*)("\\S+")(\\s*)([=:])(\\s*)', bygroups(Whitespace, Literal.String.Double, Whitespace, Operator, Whitespace)), (builtins_re + '(\\()', bygroups(Name.Function, Punctuation)), ('(\\[)([a-z_,\\s]+)(\\])', bygroups(Punctuation, Name.Builtin, Punctuation)), (classes_re + '(\\s+)("[0-9a-zA-Z-_]+")?(\\s*)("[0-9a-zA-Z-_]+")(\\s+)(\\{)', bygroups(Keyword.Reserved, Whitespace, Name.Class, Whitespace, Name.Variable, Whitespace, Punctuation)), ('(<<-?)\\s*([a-zA-Z_]\\w*)(.*?\\n)', heredoc_callback)], 'identifier': [('\\b(var\\.[0-9a-zA-Z-_\\.\\[\\]]+)\\b', bygroups(Name.Variable)), ('\\b([0-9a-zA-Z-_\\[\\]]+\\.[0-9a-zA-Z-_\\.\\[\\]]+)\\b', bygroups(Name.Variable))], 'punctuation': [('[\\[\\]()\\{\\},.?:!=]', Punctuation)], 'comment': [('[^*/]', Comment.Multiline), ('/\\*', Comment.Multiline, '#push'), ('\\*/', Comment.Multiline, '#pop'), ('[*/]', Comment.Multiline)], 'whitespace': [('\\n', Whitespace), ('\\s+', Whitespace), ('(\\\\)(\\n)', bygroups(Text, Whitespace))]}

class TermcapLexer(RegexLexer):
    """
    Lexer for termcap database source.

    This is very simple and minimal.
    """
    name = 'Termcap'
    aliases = ['termcap']
    filenames = ['termcap', 'termcap.src']
    mimetypes = []
    url = 'https://en.wikipedia.org/wiki/Termcap'
    version_added = '2.1'
    tokens = {'root': [('^#.*', Comment), ('^[^\\s#:|]+', Name.Tag, 'names'), ('\\s+', Whitespace)], 'names': [('\\n', Whitespace, '#pop'), (':', Punctuation, 'defs'), ('\\|', Punctuation), ('[^:|]+', Name.Attribute)], 'defs': [('(\\\\)(\\n[ \\t]*)', bygroups(Text, Whitespace)), ('\\n[ \\t]*', Whitespace, '#pop:2'), ('(#)([0-9]+)', bygroups(Operator, Number)), ('=', Operator, 'data'), (':', Punctuation), ('[^\\s:=#]+', Name.Class)], 'data': [('\\\\072', Literal), (':', Punctuation, '#pop'), ('[^:\\\\]+', Literal), ('.', Literal)]}

class TerminfoLexer(RegexLexer):
    """
    Lexer for terminfo database source.

    This is very simple and minimal.
    """
    name = 'Terminfo'
    aliases = ['terminfo']
    filenames = ['terminfo', 'terminfo.src']
    mimetypes = []
    url = 'https://en.wikipedia.org/wiki/Terminfo'
    version_added = '2.1'
    tokens = {'root': [('^#.*$', Comment), ('^[^\\s#,|]+', Name.Tag, 'names'), ('\\s+', Whitespace)], 'names': [('\\n', Whitespace, '#pop'), ('(,)([ \\t]*)', bygroups(Punctuation, Whitespace), 'defs'), ('\\|', Punctuation), ('[^,|]+', Name.Attribute)], 'defs': [('\\n[ \\t]+', Whitespace), ('\\n', Whitespace, '#pop:2'), ('(#)([0-9]+)', bygroups(Operator, Number)), ('=', Operator, 'data'), ('(,)([ \\t]*)', bygroups(Punctuation, Whitespace)), ('[^\\s,=#]+', Name.Class)], 'data': [('\\\\[,\\\\]', Literal), ('(,)([ \\t]*)', bygroups(Punctuation, Whitespace), '#pop'), ('[^\\\\,]+', Literal), ('.', Literal)]}

class PkgConfigLexer(RegexLexer):
    """
    Lexer for pkg-config
    (see also `manual page <http://linux.die.net/man/1/pkg-config>`_).
    """
    name = 'PkgConfig'
    url = 'http://www.freedesktop.org/wiki/Software/pkg-config/'
    aliases = ['pkgconfig']
    filenames = ['*.pc']
    mimetypes = []
    version_added = '2.1'
    tokens = {'root': [('#.*$', Comment.Single), ('^(\\w+)(=)', bygroups(Name.Attribute, Operator)), ('^([\\w.]+)(:)', bygroups(Name.Tag, Punctuation), 'spvalue'), include('interp'), ('\\s+', Whitespace), ('[^${}#=:\\n.]+', Text), ('.', Text)], 'interp': [('\\$\\$', Text), ('\\$\\{', String.Interpol, 'curly')], 'curly': [('\\}', String.Interpol, '#pop'), ('\\w+', Name.Attribute)], 'spvalue': [include('interp'), ('#.*$', Comment.Single, '#pop'), ('\\n', Whitespace, '#pop'), ('\\s+', Whitespace), ('[^${}#\\n\\s]+', Text), ('.', Text)]}

class PacmanConfLexer(RegexLexer):
    """
    Lexer for pacman.conf.

    Actually, IniLexer works almost fine for this format,
    but it yield error token. It is because pacman.conf has
    a form without assignment like:

        UseSyslog
        Color
        TotalDownload
        CheckSpace
        VerbosePkgLists

    These are flags to switch on.
    """
    name = 'PacmanConf'
    url = 'https://www.archlinux.org/pacman/pacman.conf.5.html'
    aliases = ['pacmanconf']
    filenames = ['pacman.conf']
    mimetypes = []
    version_added = '2.1'
    tokens = {'root': [('#.*$', Comment.Single), ('^(\\s*)(\\[.*?\\])(\\s*)$', bygroups(Whitespace, Keyword, Whitespace)), ('(\\w+)(\\s*)(=)', bygroups(Name.Attribute, Whitespace, Operator)), ('^(\\s*)(\\w+)(\\s*)$', bygroups(Whitespace, Name.Attribute, Whitespace)), (words(('$repo', '$arch', '%o', '%u'), suffix='\\b'), Name.Variable), ('\\s+', Whitespace), ('.', Text)]}

class AugeasLexer(RegexLexer):
    """
    Lexer for Augeas.
    """
    name = 'Augeas'
    url = 'http://augeas.net'
    aliases = ['augeas']
    filenames = ['*.aug']
    version_added = '2.4'
    tokens = {'root': [('(module)(\\s*)([^\\s=]+)', bygroups(Keyword.Namespace, Whitespace, Name.Namespace)), ('(let)(\\s*)([^\\s=]+)', bygroups(Keyword.Declaration, Whitespace, Name.Variable)), ('(del|store|value|counter|seq|key|label|autoload|incl|excl|transform|test|get|put)(\\s+)', bygroups(Name.Builtin, Whitespace)), ('(\\()([^:]+)(\\:)(unit|string|regexp|lens|tree|filter)(\\))', bygroups(Punctuation, Name.Variable, Punctuation, Keyword.Type, Punctuation)), ('\\(\\*', Comment.Multiline, 'comment'), ('[*+\\-.;=?|]', Operator), ('[()\\[\\]{}]', Operator), ('"', String.Double, 'string'), ('\\/', String.Regex, 'regex'), ('([A-Z]\\w*)(\\.)(\\w+)', bygroups(Name.Namespace, Punctuation, Name.Variable)), ('.', Name.Variable), ('\\s+', Whitespace)], 'string': [('\\\\.', String.Escape), ('[^"]', String.Double), ('"', String.Double, '#pop')], 'regex': [('\\\\.', String.Escape), ('[^/]', String.Regex), ('\\/', String.Regex, '#pop')], 'comment': [('[^*)]', Comment.Multiline), ('\\(\\*', Comment.Multiline, '#push'), ('\\*\\)', Comment.Multiline, '#pop'), ('[)*]', Comment.Multiline)]}

class TOMLLexer(RegexLexer):
    """
    Lexer for TOML, a simple language for config files.
    """
    name = 'TOML'
    aliases = ['toml']
    filenames = ['*.toml', 'Pipfile', 'poetry.lock']
    mimetypes = ['application/toml']
    url = 'https://toml.io'
    version_added = '2.4'
    _time = '\\d\\d:\\d\\d:\\d\\d(\\.\\d+)?'
    _datetime = f'(?x)\n                  \\d\\d\\d\\d-\\d\\d-\\d\\d # date, e.g., 1988-10-27\n                (\n                  [Tt ] {_time} # optional time\n                  (\n                    [Zz]|[+-]\\d\\d:\\d\\d # optional time offset\n                  )?\n                )?\n              '
    tokens = {'root': [('\\s+', Whitespace), ('#.*', Comment.Single), include('key'), ('(=)(\\s*)', bygroups(Operator, Whitespace), 'value'), ('\\[\\[?', Keyword, 'table-key')], 'key': [('[A-Za-z0-9_-]+', Name), ('"', String.Double, 'basic-string'), ("'", String.Single, 'literal-string'), ('\\.', Punctuation)], 'table-key': [('[A-Za-z0-9_-]+', Keyword), ('"', String.Double, 'basic-string'), ("'", String.Single, 'literal-string'), ('\\.', Keyword), ('\\]\\]?', Keyword, '#pop'), ('[ \\t]+', Whitespace)], 'value': [(_datetime, Literal.Date, '#pop'), (_time, Literal.Date, '#pop'), ('[+-]?\\d[0-9_]*[eE][+-]?\\d[0-9_]*', Number.Float, '#pop'), ('[+-]?\\d[0-9_]*\\.\\d[0-9_]*([eE][+-]?\\d[0-9_]*)?', Number.Float, '#pop'), ('[+-]?(inf|nan)', Number.Float, '#pop'), ('-?0b[01_]+', Number.Bin, '#pop'), ('-?0o[0-7_]+', Number.Oct, '#pop'), ('-?0x[0-9a-fA-F_]+', Number.Hex, '#pop'), ('[+-]?[0-9_]+', Number.Integer, '#pop'), ('"""', String.Double, ('#pop', 'multiline-basic-string')), ('"', String.Double, ('#pop', 'basic-string')), ("'''", String.Single, ('#pop', 'multiline-literal-string')), ("'", String.Single, ('#pop', 'literal-string')), ('true|false', Keyword.Constant, '#pop'), ('\\[', Punctuation, ('#pop', 'array')), ('\\{', Punctuation, ('#pop', 'inline-table'))], 'array': [('\\s+', Whitespace), ('#.*', Comment.Single), (',', Punctuation), ('\\]', Punctuation, '#pop'), default('value')], 'inline-table': [('[ \\t]+', Whitespace), include('key'), ('(=)(\\s*)', bygroups(Punctuation, Whitespace), 'value'), (',', Punctuation), ('\\}', Punctuation, '#pop')], 'basic-string': [('"', String.Double, '#pop'), include('escapes'), ('[^"\\\\]+', String.Double)], 'literal-string': [(".*?'", String.Single, '#pop')], 'multiline-basic-string': [('"""', String.Double, '#pop'), ('(\\\\)(\\n)', bygroups(String.Escape, Whitespace)), include('escapes'), ('[^"\\\\]+', String.Double), ('"', String.Double)], 'multiline-literal-string': [("'''", String.Single, '#pop'), ("[^']+", String.Single), ("'", String.Single)], 'escapes': [('\\\\u[0-9a-fA-F]{4}|\\\\U[0-9a-fA-F]{8}', String.Escape), ('\\\\.', String.Escape)]}

class NestedTextLexer(RegexLexer):
    """
    Lexer for *NextedText*, a human-friendly data format.

    .. versionchanged:: 2.16
        Added support for *NextedText* v3.0.
    """
    name = 'NestedText'
    url = 'https://nestedtext.org'
    aliases = ['nestedtext', 'nt']
    filenames = ['*.nt']
    version_added = '2.9'
    tokens = {'root': [('^([ ]*)(#.*)$', bygroups(Whitespace, Comment)), ('^([ ]*)(\\{)', bygroups(Whitespace, Punctuation), 'inline_dict'), ('^([ ]*)(\\[)', bygroups(Whitespace, Punctuation), 'inline_list'), ('^([ ]*)(>)$', bygroups(Whitespace, Punctuation)), ('^([ ]*)(>)( )(.*?)([ \\t]*)$', bygroups(Whitespace, Punctuation, Whitespace, Text, Whitespace)), ('^([ ]*)(-)$', bygroups(Whitespace, Punctuation)), ('^([ ]*)(-)( )(.*?)([ \\t]*)$', bygroups(Whitespace, Punctuation, Whitespace, Text, Whitespace)), ('^([ ]*)(:)$', bygroups(Whitespace, Punctuation)), ('^([ ]*)(:)( )([^\\n]*?)([ \\t]*)$', bygroups(Whitespace, Punctuation, Whitespace, Name.Tag, Whitespace)), ('^([ ]*)([^\\{\\[\\s].*?)(:)$', bygroups(Whitespace, Name.Tag, Punctuation)), ('^([ ]*)([^\\{\\[\\s].*?)(:)( )(.*?)([ \\t]*)$', bygroups(Whitespace, Name.Tag, Punctuation, Whitespace, Text, Whitespace))], 'inline_list': [include('whitespace'), ('[^\\{\\}\\[\\],\\s]+', Text), include('inline_value'), (',', Punctuation), ('\\]', Punctuation, '#pop'), ('\\n', Error, '#pop')], 'inline_dict': [include('whitespace'), ('[^\\{\\}\\[\\],:\\s]+', Name.Tag), (':', Punctuation, 'inline_dict_value'), ('\\}', Punctuation, '#pop'), ('\\n', Error, '#pop')], 'inline_dict_value': [include('whitespace'), ('[^\\{\\}\\[\\],:\\s]+', Text), include('inline_value'), (',', Punctuation, '#pop'), ('\\}', Punctuation, '#pop:2')], 'inline_value': [include('whitespace'), ('\\{', Punctuation, 'inline_dict'), ('\\[', Punctuation, 'inline_list')], 'whitespace': [('[ \\t]+', Whitespace)]}

class SingularityLexer(RegexLexer):
    """
    Lexer for Singularity definition files.
    """
    name = 'Singularity'
    url = 'https://www.sylabs.io/guides/3.0/user-guide/definition_files.html'
    aliases = ['singularity']
    filenames = ['*.def', 'Singularity']
    version_added = '2.6'
    flags = re.IGNORECASE | re.MULTILINE | re.DOTALL
    _headers = '^(\\s*)(bootstrap|from|osversion|mirrorurl|include|registry|namespace|includecmd)(:)'
    _section = '^(%(?:pre|post|setup|environment|help|labels|test|runscript|files|startscript))(\\s*)'
    _appsect = '^(%app(?:install|help|run|labels|env|test|files))(\\s*)'
    tokens = {'root': [(_section, bygroups(Generic.Heading, Whitespace), 'script'), (_appsect, bygroups(Generic.Heading, Whitespace), 'script'), (_headers, bygroups(Whitespace, Keyword, Text)), ('\\s*#.*?\\n', Comment), ('\\b(([0-9]+\\.?[0-9]*)|(\\.[0-9]+))\\b', Number), ('[ \\t]+', Whitespace), ('(?!^\\s*%).', Text)], 'script': [('(.+?(?=^\\s*%))|(.*)', using(BashLexer), '#pop')]}

    def analyse_text(text):
        """This is a quite simple script file, but there are a few keywords
        which seem unique to this language."""
        result = 0
        if re.search('\\b(?:osversion|includecmd|mirrorurl)\\b', text, re.IGNORECASE):
            result += 0.5
        if re.search(SingularityLexer._section[1:], text):
            result += 0.49
        return result

class UnixConfigLexer(RegexLexer):
    """
    Lexer for Unix/Linux config files using colon-separated values, e.g.

    * ``/etc/group``
    * ``/etc/passwd``
    * ``/etc/shadow``
    """
    name = 'Unix/Linux config files'
    aliases = ['unixconfig', 'linuxconfig']
    filenames = []
    url = 'https://en.wikipedia.org/wiki/Configuration_file#Unix_and_Unix-like_operating_systems'
    version_added = '2.12'
    tokens = {'root': [('^#.*', Comment), ('\\n', Whitespace), (':', Punctuation), ('[0-9]+', Number), ('((?!\\n)[a-zA-Z0-9\\_\\-\\s\\(\\),]){2,}', Text), ('[^:\\n]+', String)]}
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel, ConfigDict
from typing import Optional
from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.config import get_config, save_config
from open_webui.config import BannerModel
from open_webui.utils.tools import get_tool_server_data, get_tool_servers_data, get_tool_server_url
router = APIRouter()

class ImportConfigForm(BaseModel):
    config: dict

@router.post('/import', response_model=dict)
async def import_config(form_data: ImportConfigForm, user=Depends(get_admin_user)):
    save_config(form_data.config)
    return get_config()

@router.get('/export', response_model=dict)
async def export_config(user=Depends(get_admin_user)):
    return get_config()

class ConnectionsConfigForm(BaseModel):
    ENABLE_DIRECT_CONNECTIONS: bool
    ENABLE_BASE_MODELS_CACHE: bool

@router.get('/connections', response_model=ConnectionsConfigForm)
async def get_connections_config(request: Request, user=Depends(get_admin_user)):
    return {'ENABLE_DIRECT_CONNECTIONS': request.app.state.config.ENABLE_DIRECT_CONNECTIONS, 'ENABLE_BASE_MODELS_CACHE': request.app.state.config.ENABLE_BASE_MODELS_CACHE}

@router.post('/connections', response_model=ConnectionsConfigForm)
async def set_connections_config(request: Request, form_data: ConnectionsConfigForm, user=Depends(get_admin_user)):
    request.app.state.config.ENABLE_DIRECT_CONNECTIONS = form_data.ENABLE_DIRECT_CONNECTIONS
    request.app.state.config.ENABLE_BASE_MODELS_CACHE = form_data.ENABLE_BASE_MODELS_CACHE
    return {'ENABLE_DIRECT_CONNECTIONS': request.app.state.config.ENABLE_DIRECT_CONNECTIONS, 'ENABLE_BASE_MODELS_CACHE': request.app.state.config.ENABLE_BASE_MODELS_CACHE}

class ToolServerConnection(BaseModel):
    url: str
    path: str
    auth_type: Optional[str]
    key: Optional[str]
    config: Optional[dict]
    model_config = ConfigDict(extra='allow')

class ToolServersConfigForm(BaseModel):
    TOOL_SERVER_CONNECTIONS: list[ToolServerConnection]

@router.get('/tool_servers', response_model=ToolServersConfigForm)
async def get_tool_servers_config(request: Request, user=Depends(get_admin_user)):
    return {'TOOL_SERVER_CONNECTIONS': request.app.state.config.TOOL_SERVER_CONNECTIONS}

@router.post('/tool_servers', response_model=ToolServersConfigForm)
async def set_tool_servers_config(request: Request, form_data: ToolServersConfigForm, user=Depends(get_admin_user)):
    request.app.state.config.TOOL_SERVER_CONNECTIONS = [connection.model_dump() for connection in form_data.TOOL_SERVER_CONNECTIONS]
    request.app.state.TOOL_SERVERS = await get_tool_servers_data(request.app.state.config.TOOL_SERVER_CONNECTIONS)
    return {'TOOL_SERVER_CONNECTIONS': request.app.state.config.TOOL_SERVER_CONNECTIONS}

@router.post('/tool_servers/verify')
async def verify_tool_servers_config(request: Request, form_data: ToolServerConnection, user=Depends(get_admin_user)):
    """
    Verify the connection to the tool server.
    """
    try:
        token = None
        if form_data.auth_type == 'bearer':
            token = form_data.key
        elif form_data.auth_type == 'session':
            token = request.state.token.credentials
        url = get_tool_server_url(form_data.url, form_data.path)
        return await get_tool_server_data(token, url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Failed to connect to the tool server: {str(e)}')

class CodeInterpreterConfigForm(BaseModel):
    ENABLE_CODE_EXECUTION: bool
    CODE_EXECUTION_ENGINE: str
    CODE_EXECUTION_JUPYTER_URL: Optional[str]
    CODE_EXECUTION_JUPYTER_AUTH: Optional[str]
    CODE_EXECUTION_JUPYTER_AUTH_TOKEN: Optional[str]
    CODE_EXECUTION_JUPYTER_AUTH_PASSWORD: Optional[str]
    CODE_EXECUTION_JUPYTER_TIMEOUT: Optional[int]
    ENABLE_CODE_INTERPRETER: bool
    CODE_INTERPRETER_ENGINE: str
    CODE_INTERPRETER_PROMPT_TEMPLATE: Optional[str]
    CODE_INTERPRETER_JUPYTER_URL: Optional[str]
    CODE_INTERPRETER_JUPYTER_AUTH: Optional[str]
    CODE_INTERPRETER_JUPYTER_AUTH_TOKEN: Optional[str]
    CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD: Optional[str]
    CODE_INTERPRETER_JUPYTER_TIMEOUT: Optional[int]

@router.get('/code_execution', response_model=CodeInterpreterConfigForm)
async def get_code_execution_config(request: Request, user=Depends(get_admin_user)):
    return {'ENABLE_CODE_EXECUTION': request.app.state.config.ENABLE_CODE_EXECUTION, 'CODE_EXECUTION_ENGINE': request.app.state.config.CODE_EXECUTION_ENGINE, 'CODE_EXECUTION_JUPYTER_URL': request.app.state.config.CODE_EXECUTION_JUPYTER_URL, 'CODE_EXECUTION_JUPYTER_AUTH': request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH, 'CODE_EXECUTION_JUPYTER_AUTH_TOKEN': request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH_TOKEN, 'CODE_EXECUTION_JUPYTER_AUTH_PASSWORD': request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH_PASSWORD, 'CODE_EXECUTION_JUPYTER_TIMEOUT': request.app.state.config.CODE_EXECUTION_JUPYTER_TIMEOUT, 'ENABLE_CODE_INTERPRETER': request.app.state.config.ENABLE_CODE_INTERPRETER, 'CODE_INTERPRETER_ENGINE': request.app.state.config.CODE_INTERPRETER_ENGINE, 'CODE_INTERPRETER_PROMPT_TEMPLATE': request.app.state.config.CODE_INTERPRETER_PROMPT_TEMPLATE, 'CODE_INTERPRETER_JUPYTER_URL': request.app.state.config.CODE_INTERPRETER_JUPYTER_URL, 'CODE_INTERPRETER_JUPYTER_AUTH': request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH, 'CODE_INTERPRETER_JUPYTER_AUTH_TOKEN': request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH_TOKEN, 'CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD': request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD, 'CODE_INTERPRETER_JUPYTER_TIMEOUT': request.app.state.config.CODE_INTERPRETER_JUPYTER_TIMEOUT}

@router.post('/code_execution', response_model=CodeInterpreterConfigForm)
async def set_code_execution_config(request: Request, form_data: CodeInterpreterConfigForm, user=Depends(get_admin_user)):
    request.app.state.config.ENABLE_CODE_EXECUTION = form_data.ENABLE_CODE_EXECUTION
    request.app.state.config.CODE_EXECUTION_ENGINE = form_data.CODE_EXECUTION_ENGINE
    request.app.state.config.CODE_EXECUTION_JUPYTER_URL = form_data.CODE_EXECUTION_JUPYTER_URL
    request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH = form_data.CODE_EXECUTION_JUPYTER_AUTH
    request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH_TOKEN = form_data.CODE_EXECUTION_JUPYTER_AUTH_TOKEN
    request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH_PASSWORD = form_data.CODE_EXECUTION_JUPYTER_AUTH_PASSWORD
    request.app.state.config.CODE_EXECUTION_JUPYTER_TIMEOUT = form_data.CODE_EXECUTION_JUPYTER_TIMEOUT
    request.app.state.config.ENABLE_CODE_INTERPRETER = form_data.ENABLE_CODE_INTERPRETER
    request.app.state.config.CODE_INTERPRETER_ENGINE = form_data.CODE_INTERPRETER_ENGINE
    request.app.state.config.CODE_INTERPRETER_PROMPT_TEMPLATE = form_data.CODE_INTERPRETER_PROMPT_TEMPLATE
    request.app.state.config.CODE_INTERPRETER_JUPYTER_URL = form_data.CODE_INTERPRETER_JUPYTER_URL
    request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH = form_data.CODE_INTERPRETER_JUPYTER_AUTH
    request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH_TOKEN = form_data.CODE_INTERPRETER_JUPYTER_AUTH_TOKEN
    request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD = form_data.CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD
    request.app.state.config.CODE_INTERPRETER_JUPYTER_TIMEOUT = form_data.CODE_INTERPRETER_JUPYTER_TIMEOUT
    return {'ENABLE_CODE_EXECUTION': request.app.state.config.ENABLE_CODE_EXECUTION, 'CODE_EXECUTION_ENGINE': request.app.state.config.CODE_EXECUTION_ENGINE, 'CODE_EXECUTION_JUPYTER_URL': request.app.state.config.CODE_EXECUTION_JUPYTER_URL, 'CODE_EXECUTION_JUPYTER_AUTH': request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH, 'CODE_EXECUTION_JUPYTER_AUTH_TOKEN': request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH_TOKEN, 'CODE_EXECUTION_JUPYTER_AUTH_PASSWORD': request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH_PASSWORD, 'CODE_EXECUTION_JUPYTER_TIMEOUT': request.app.state.config.CODE_EXECUTION_JUPYTER_TIMEOUT, 'ENABLE_CODE_INTERPRETER': request.app.state.config.ENABLE_CODE_INTERPRETER, 'CODE_INTERPRETER_ENGINE': request.app.state.config.CODE_INTERPRETER_ENGINE, 'CODE_INTERPRETER_PROMPT_TEMPLATE': request.app.state.config.CODE_INTERPRETER_PROMPT_TEMPLATE, 'CODE_INTERPRETER_JUPYTER_URL': request.app.state.config.CODE_INTERPRETER_JUPYTER_URL, 'CODE_INTERPRETER_JUPYTER_AUTH': request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH, 'CODE_INTERPRETER_JUPYTER_AUTH_TOKEN': request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH_TOKEN, 'CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD': request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD, 'CODE_INTERPRETER_JUPYTER_TIMEOUT': request.app.state.config.CODE_INTERPRETER_JUPYTER_TIMEOUT}

class ModelsConfigForm(BaseModel):
    DEFAULT_MODELS: Optional[str]
    MODEL_ORDER_LIST: Optional[list[str]]

@router.get('/models', response_model=ModelsConfigForm)
async def get_models_config(request: Request, user=Depends(get_admin_user)):
    return {'DEFAULT_MODELS': request.app.state.config.DEFAULT_MODELS, 'MODEL_ORDER_LIST': request.app.state.config.MODEL_ORDER_LIST}

@router.post('/models', response_model=ModelsConfigForm)
async def set_models_config(request: Request, form_data: ModelsConfigForm, user=Depends(get_admin_user)):
    request.app.state.config.DEFAULT_MODELS = form_data.DEFAULT_MODELS
    request.app.state.config.MODEL_ORDER_LIST = form_data.MODEL_ORDER_LIST
    return {'DEFAULT_MODELS': request.app.state.config.DEFAULT_MODELS, 'MODEL_ORDER_LIST': request.app.state.config.MODEL_ORDER_LIST}

class PromptSuggestion(BaseModel):
    title: list[str]
    content: str

class SetDefaultSuggestionsForm(BaseModel):
    suggestions: list[PromptSuggestion]

@router.post('/suggestions', response_model=list[PromptSuggestion])
async def set_default_suggestions(request: Request, form_data: SetDefaultSuggestionsForm, user=Depends(get_admin_user)):
    data = form_data.model_dump()
    request.app.state.config.DEFAULT_PROMPT_SUGGESTIONS = data['suggestions']
    return request.app.state.config.DEFAULT_PROMPT_SUGGESTIONS

class SetBannersForm(BaseModel):
    banners: list[BannerModel]

@router.post('/banners', response_model=list[BannerModel])
async def set_banners(request: Request, form_data: SetBannersForm, user=Depends(get_admin_user)):
    data = form_data.model_dump()
    request.app.state.config.BANNERS = data['banners']
    return request.app.state.config.BANNERS

@router.get('/banners', response_model=list[BannerModel])
async def get_banners(request: Request, user=Depends(get_verified_user)):
    return request.app.state.config.BANNERS
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from open_webui.config import BannerModel, get_config, save_config
from open_webui.local_pipelines.runner import get_local_pipelines, is_chat_pipelines_enabled, set_chat_pipelines_enabled, set_local_pipelines
from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.utils.tools import get_tool_server_data, get_tool_server_url, get_tool_servers_data
from pydantic import BaseModel, ConfigDict, Field
router = APIRouter()

class LocalPipelinesConfigForm(BaseModel):
    pipelines: list[str] = Field(default_factory=list)
    enable_for_chat: bool = False

@router.get('/local_pipelines', response_model=LocalPipelinesConfigForm)
async def get_local_pipelines_config(user=Depends(get_admin_user)):
    return LocalPipelinesConfigForm(pipelines=get_local_pipelines(), enable_for_chat=is_chat_pipelines_enabled())

@router.post('/local_pipelines', response_model=LocalPipelinesConfigForm)
async def set_local_pipelines_config(form_data: LocalPipelinesConfigForm, user=Depends(get_admin_user)):
    set_local_pipelines(form_data.pipelines)
    set_chat_pipelines_enabled(form_data.enable_for_chat)
    return LocalPipelinesConfigForm(pipelines=get_local_pipelines(), enable_for_chat=is_chat_pipelines_enabled())

@router.post('/import', response_model=dict)
async def import_config(form_data: ImportConfigForm, user=Depends(get_admin_user)):
    save_config(form_data.config)
    return get_config()

@router.get('/export', response_model=dict)
async def export_config(user=Depends(get_admin_user)):
    return get_config()

@router.get('/connections', response_model=ConnectionsConfigForm)
async def get_connections_config(request: Request, user=Depends(get_admin_user)):
    return {'ENABLE_DIRECT_CONNECTIONS': request.app.state.config.ENABLE_DIRECT_CONNECTIONS, 'ENABLE_BASE_MODELS_CACHE': request.app.state.config.ENABLE_BASE_MODELS_CACHE}

@router.post('/connections', response_model=ConnectionsConfigForm)
async def set_connections_config(request: Request, form_data: ConnectionsConfigForm, user=Depends(get_admin_user)):
    request.app.state.config.ENABLE_DIRECT_CONNECTIONS = form_data.ENABLE_DIRECT_CONNECTIONS
    request.app.state.config.ENABLE_BASE_MODELS_CACHE = form_data.ENABLE_BASE_MODELS_CACHE
    return {'ENABLE_DIRECT_CONNECTIONS': request.app.state.config.ENABLE_DIRECT_CONNECTIONS, 'ENABLE_BASE_MODELS_CACHE': request.app.state.config.ENABLE_BASE_MODELS_CACHE}

@router.get('/tool_servers', response_model=ToolServersConfigForm)
async def get_tool_servers_config(request: Request, user=Depends(get_admin_user)):
    return {'TOOL_SERVER_CONNECTIONS': request.app.state.config.TOOL_SERVER_CONNECTIONS}

@router.post('/tool_servers', response_model=ToolServersConfigForm)
async def set_tool_servers_config(request: Request, form_data: ToolServersConfigForm, user=Depends(get_admin_user)):
    request.app.state.config.TOOL_SERVER_CONNECTIONS = [connection.model_dump() for connection in form_data.TOOL_SERVER_CONNECTIONS]
    request.app.state.TOOL_SERVERS = await get_tool_servers_data(request.app.state.config.TOOL_SERVER_CONNECTIONS)
    return {'TOOL_SERVER_CONNECTIONS': request.app.state.config.TOOL_SERVER_CONNECTIONS}

@router.post('/tool_servers/verify')
async def verify_tool_servers_config(request: Request, form_data: ToolServerConnection, user=Depends(get_admin_user)):
    """
    Verify the connection to the tool server.
    """
    try:
        token = None
        if form_data.auth_type == 'bearer':
            token = form_data.key
        elif form_data.auth_type == 'session':
            token = request.state.token.credentials
        url = get_tool_server_url(form_data.url, form_data.path)
        return await get_tool_server_data(token, url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Failed to connect to the tool server: {str(e)}')

@router.get('/code_execution', response_model=CodeInterpreterConfigForm)
async def get_code_execution_config(request: Request, user=Depends(get_admin_user)):
    return {'ENABLE_CODE_EXECUTION': request.app.state.config.ENABLE_CODE_EXECUTION, 'CODE_EXECUTION_ENGINE': request.app.state.config.CODE_EXECUTION_ENGINE, 'CODE_EXECUTION_JUPYTER_URL': request.app.state.config.CODE_EXECUTION_JUPYTER_URL, 'CODE_EXECUTION_JUPYTER_AUTH': request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH, 'CODE_EXECUTION_JUPYTER_AUTH_TOKEN': request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH_TOKEN, 'CODE_EXECUTION_JUPYTER_AUTH_PASSWORD': request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH_PASSWORD, 'CODE_EXECUTION_JUPYTER_TIMEOUT': request.app.state.config.CODE_EXECUTION_JUPYTER_TIMEOUT, 'ENABLE_CODE_INTERPRETER': request.app.state.config.ENABLE_CODE_INTERPRETER, 'CODE_INTERPRETER_ENGINE': request.app.state.config.CODE_INTERPRETER_ENGINE, 'CODE_INTERPRETER_PROMPT_TEMPLATE': request.app.state.config.CODE_INTERPRETER_PROMPT_TEMPLATE, 'CODE_INTERPRETER_JUPYTER_URL': request.app.state.config.CODE_INTERPRETER_JUPYTER_URL, 'CODE_INTERPRETER_JUPYTER_AUTH': request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH, 'CODE_INTERPRETER_JUPYTER_AUTH_TOKEN': request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH_TOKEN, 'CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD': request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD, 'CODE_INTERPRETER_JUPYTER_TIMEOUT': request.app.state.config.CODE_INTERPRETER_JUPYTER_TIMEOUT}

@router.post('/code_execution', response_model=CodeInterpreterConfigForm)
async def set_code_execution_config(request: Request, form_data: CodeInterpreterConfigForm, user=Depends(get_admin_user)):
    request.app.state.config.ENABLE_CODE_EXECUTION = form_data.ENABLE_CODE_EXECUTION
    request.app.state.config.CODE_EXECUTION_ENGINE = form_data.CODE_EXECUTION_ENGINE
    request.app.state.config.CODE_EXECUTION_JUPYTER_URL = form_data.CODE_EXECUTION_JUPYTER_URL
    request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH = form_data.CODE_EXECUTION_JUPYTER_AUTH
    request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH_TOKEN = form_data.CODE_EXECUTION_JUPYTER_AUTH_TOKEN
    request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH_PASSWORD = form_data.CODE_EXECUTION_JUPYTER_AUTH_PASSWORD
    request.app.state.config.CODE_EXECUTION_JUPYTER_TIMEOUT = form_data.CODE_EXECUTION_JUPYTER_TIMEOUT
    request.app.state.config.ENABLE_CODE_INTERPRETER = form_data.ENABLE_CODE_INTERPRETER
    request.app.state.config.CODE_INTERPRETER_ENGINE = form_data.CODE_INTERPRETER_ENGINE
    request.app.state.config.CODE_INTERPRETER_PROMPT_TEMPLATE = form_data.CODE_INTERPRETER_PROMPT_TEMPLATE
    request.app.state.config.CODE_INTERPRETER_JUPYTER_URL = form_data.CODE_INTERPRETER_JUPYTER_URL
    request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH = form_data.CODE_INTERPRETER_JUPYTER_AUTH
    request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH_TOKEN = form_data.CODE_INTERPRETER_JUPYTER_AUTH_TOKEN
    request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD = form_data.CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD
    request.app.state.config.CODE_INTERPRETER_JUPYTER_TIMEOUT = form_data.CODE_INTERPRETER_JUPYTER_TIMEOUT
    return {'ENABLE_CODE_EXECUTION': request.app.state.config.ENABLE_CODE_EXECUTION, 'CODE_EXECUTION_ENGINE': request.app.state.config.CODE_EXECUTION_ENGINE, 'CODE_EXECUTION_JUPYTER_URL': request.app.state.config.CODE_EXECUTION_JUPYTER_URL, 'CODE_EXECUTION_JUPYTER_AUTH': request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH, 'CODE_EXECUTION_JUPYTER_AUTH_TOKEN': request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH_TOKEN, 'CODE_EXECUTION_JUPYTER_AUTH_PASSWORD': request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH_PASSWORD, 'CODE_EXECUTION_JUPYTER_TIMEOUT': request.app.state.config.CODE_EXECUTION_JUPYTER_TIMEOUT, 'ENABLE_CODE_INTERPRETER': request.app.state.config.ENABLE_CODE_INTERPRETER, 'CODE_INTERPRETER_ENGINE': request.app.state.config.CODE_INTERPRETER_ENGINE, 'CODE_INTERPRETER_PROMPT_TEMPLATE': request.app.state.config.CODE_INTERPRETER_PROMPT_TEMPLATE, 'CODE_INTERPRETER_JUPYTER_URL': request.app.state.config.CODE_INTERPRETER_JUPYTER_URL, 'CODE_INTERPRETER_JUPYTER_AUTH': request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH, 'CODE_INTERPRETER_JUPYTER_AUTH_TOKEN': request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH_TOKEN, 'CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD': request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD, 'CODE_INTERPRETER_JUPYTER_TIMEOUT': request.app.state.config.CODE_INTERPRETER_JUPYTER_TIMEOUT}

@router.get('/models', response_model=ModelsConfigForm)
async def get_models_config(request: Request, user=Depends(get_admin_user)):
    return {'DEFAULT_MODELS': request.app.state.config.DEFAULT_MODELS, 'MODEL_ORDER_LIST': request.app.state.config.MODEL_ORDER_LIST}

@router.post('/models', response_model=ModelsConfigForm)
async def set_models_config(request: Request, form_data: ModelsConfigForm, user=Depends(get_admin_user)):
    request.app.state.config.DEFAULT_MODELS = form_data.DEFAULT_MODELS
    request.app.state.config.MODEL_ORDER_LIST = form_data.MODEL_ORDER_LIST
    return {'DEFAULT_MODELS': request.app.state.config.DEFAULT_MODELS, 'MODEL_ORDER_LIST': request.app.state.config.MODEL_ORDER_LIST}

@router.post('/suggestions', response_model=list[PromptSuggestion])
async def set_default_suggestions(request: Request, form_data: SetDefaultSuggestionsForm, user=Depends(get_admin_user)):
    data = form_data.model_dump()
    request.app.state.config.DEFAULT_PROMPT_SUGGESTIONS = data['suggestions']
    return request.app.state.config.DEFAULT_PROMPT_SUGGESTIONS

@router.post('/banners', response_model=list[BannerModel])
async def set_banners(request: Request, form_data: SetBannersForm, user=Depends(get_admin_user)):
    data = form_data.model_dump()
    request.app.state.config.BANNERS = data['banners']
    return request.app.state.config.BANNERS

@router.get('/banners', response_model=list[BannerModel])
async def get_banners(request: Request, user=Depends(get_verified_user)):
    return request.app.state.config.BANNERS