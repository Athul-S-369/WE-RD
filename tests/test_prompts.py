from weird.llm.prompts import load_prompt, prompts_dir, render_prompt


def test_prompts_resolve_and_render():
    assert prompts_dir().is_dir()
    text = load_prompt("analyze")
    assert "WE-RD" in text or "technical analysis" in text.lower()
    rendered = render_prompt("classify", title="A compiler in a weekend", source="demo", text="LLVM")
    assert "A compiler in a weekend" in rendered
    assert "{{title}}" not in rendered
