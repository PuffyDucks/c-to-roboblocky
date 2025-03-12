import clang.cindex

clang.cindex.Config.set_library_file('/usr/lib64/libclang.so.19.1.5')
index = clang.cindex.Index.create()
tu = index.parse('/home/luna/src/barobo/c-to-blocks/example.c')

def print_ast(node, indent=0):
    print(' ' * indent + f'{node.kind} {node.spelling} {node.type.spelling}')
    for child in node.get_children():
        print_ast(child, indent + 2)

print_ast(tu.cursor)
