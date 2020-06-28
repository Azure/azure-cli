import itertools
import re


def filter_for_env(value, name):
    current = (
        set(itertools.chain.from_iterable([(i for i, _ in a) for a in find_factor_groups(name)]))
        if name is not None
        else set()
    )
    overall = []
    for factors, content in expand_factors(value):
        if factors is None:
            overall.append(content)
        else:
            for group in factors:
                for name, negate in group:
                    contains = name in current
                    if contains == negate:
                        break
                else:
                    overall.append(content)
    result = "\n".join(overall)
    return result


def find_envs(value):
    seen = set()
    for factors, _ in expand_factors(value):
        if factors is not None:
            for group in factors:
                env = explode_factor(group)
                if env not in seen:
                    yield env
                    seen.add(env)


def extend_factors(value):
    for group in find_factor_groups(value):
        yield explode_factor(group)


def explode_factor(group):
    return "-".join([name for name, _ in group])


def expand_factors(value):
    for line in value.split("\n"):
        match = re.match(r"^((?P<factor_expr>[\w{}.!,-]+):\s+)?(?P<content>.*?)$", line)
        groups = match.groupdict()
        factor_expr, content = groups["factor_expr"], groups["content"]
        if factor_expr is not None:
            factors = find_factor_groups(factor_expr)
            yield factors, content
        else:
            yield None, content


def is_negated(factor):
    return factor.startswith("!")


def name_with_negate(factor):
    negated = is_negated(factor)
    return (factor[1:] if negated else factor), negated


def find_factor_groups(value):
    """transform '{py,!pi}-{a,b},c' to [{'py', 'a'}, {'py', 'b'}, {'pi', 'a'}, {'pi', 'b'}, {'c'}]"""
    for env in expand_env_with_negation(value):
        yield (name_with_negate(f) for f in env.split("-"))


def expand_env_with_negation(value):
    """transform '{py,!pi}-{a,b},c' to ['py-a', 'py-b', '!pi-a', '!pi-b', 'c']"""
    for key, group in itertools.groupby(re.split(r"((?:{[^}]+\})+)|,", value), key=bool):
        if key:
            group_str = "".join(group).strip()
            elements = re.split(r"{([^}]+)\}", group_str)
            parts = [re.sub(r"\s+", "", elem).split(",") for elem in elements]
            for variant in itertools.product(*parts):
                variant_str = "".join(variant)
                yield variant_str


__all__ = ("filter_for_env", "find_envs", "expand_factors", "extend_factors")
