
import javalang as jl
from javalang.tree import ClassCreator, FieldDeclaration, ClassDeclaration, MethodInvocation, Expression, MemberReference

from .helpers import find

# ================================
JAVA_BLOCKS_PATH = "minecraft_code/Blocks.java"

BlockEntry = tuple[str, str, str]  # (const_name, snake_name, material?)
BLOCK_REGISTRY: dict[str, BlockEntry] = {}

with open(JAVA_BLOCKS_PATH, "r", encoding="utf-8") as f:
    file_tree = jl.parse.parse(f.read())
    _, cla = next(file_tree.filter(ClassDeclaration))
    JAVA_BLOCKS_CLASS: ClassDeclaration = cla

# ================================
def properties_call(expr: Expression) -> bool:
    if not isinstance(expr, MethodInvocation):
        return False
    qua  = expr.qualifier
    return qua == "Properties"

def materials_ref(expr: MemberReference) -> bool:
    if not isinstance(expr, MemberReference):
        print(type(expr))
        return False
    qua  = expr.qualifier
    # name = expr.member
    # print(qua, name)
    return qua == "Material"

def block_call_material(new_block_call: ClassCreator):
    block_args: list[Expression] = new_block_call.arguments
    properties_arg: MethodInvocation | None = find(block_args, properties_call)
    assert properties_arg is not None

    if properties_arg.member == "of":
        refs = properties_arg.filter(MemberReference)
        material_ref = find(refs, lambda tup: materials_ref(tup[1]))[1]
        assert material_ref is not None
        material = material_ref.member
        return material
    if properties_arg.member == "copy":
        args = properties_arg.arguments
        assert len(args) == 1
        arg = args[0]
        name = arg.member
        # assume the other block was already registered
        _, _, material = BLOCK_REGISTRY[name]
        return material
    assert False, "Unknown properties method"

def get_block_fields(field: FieldDeclaration) -> tuple[str, str, str]:
    """(const_name, snake_name, material?)"""
    content = field.declarators[0]
    const_name = content.name
    init = content.initializer
    assert isinstance(init, MethodInvocation)

    args = init.arguments
    snake_name_quoted: str = args[0].value
    snake_name = snake_name_quoted[1:-1]
    new_block_call = args[1]

    material = (
        block_call_material(new_block_call)
        if isinstance(new_block_call, ClassCreator)
        else "")

    return (const_name, snake_name, material)

def populate_block_registry() -> None:
    """populate BLOCK_REGISTRY with (const_name, snake_name, material?)"""
    for field in JAVA_BLOCKS_CLASS.fields:
        fields = get_block_fields(field)
        BLOCK_REGISTRY[fields[0]] = fields

populate_block_registry()