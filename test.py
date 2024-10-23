import clang.cindex

# Path to the libclang shared library (adjust this for your system)
clang.cindex.Config.set_library_file('/usr/lib64/libclang.so.17.0.6')

# Initialize index
index = clang.cindex.Index.create()

# Parse the C file
tu = index.parse('/home/luna/src/c-to-roboblocky/example.c')

# Walk through the AST and print nodes
def print_ast(node, indent=0):
    print(' ' * indent + f'{node.kind} {node.spelling}')
    for child in node.get_children():
        print_ast(child, indent + 2)

# Start from the root node
print_ast(tu.cursor)
