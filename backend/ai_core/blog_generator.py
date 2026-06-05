from .prompts import build_prompt, build_tag_prompt, get_current_time
from .provider_manager import ProviderManager


def generate_blog(problem, credentials: dict | None = None) -> str:

    current_time = get_current_time(problem)

    prompt = build_prompt(
        problem,
        current_time,
    )

    manager = ProviderManager()

    if credentials:
        return manager.generate(prompt, credentials)
    return manager.generate(prompt)



def generate_tags(
    problem,
    blog_content: str,
    credentials: dict | None = None,
) -> str:

    prompt = build_tag_prompt(
        problem,
        blog_content,
    )

    manager = ProviderManager()

    if credentials:
        return manager.generate(prompt, credentials)

    return manager.generate(prompt)
