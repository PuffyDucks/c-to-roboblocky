# Installing Dependencies
To install the required dependencies, run the following command:
```sh
pip3 install libclang pyyaml
```

# Transpiler Quirks
Some quirks documented for reference. Most are due to limitations in RoboBlocky.

## functions
- The function `main` will not generate a function block. Instead, the statements will be placed directly into RoboBlocky. 
- Parameter names and variable names across all functions must be unique.
- Functions cannot be recursive. 
- Parameter typing is ignored. 
- Return typing is also ignored _unless_ the return type is `void` - then a block with no return will be used.
- The return slot on function blocks will always be empty. 
- Return statements in C are converted into conditional return blocks.
    - These blocks will have the condition set to `true`.
    - e.g. in C: `return 0;` becomes in RoboBlocky: `if (true) return 0;`
- Function names PI, E, and INFINITY are reserved for constants.

## if statements
Works with one liners, e.g.: 
```c
if (t < 0) return 4;
else if (t > 4) return 1;
else return 2;
```

## for statements
- For statements in RoboBlocky are limited to iteration of an integer.
- Thus, for loops are required to: 
    - Initialize a variable
    - Use a comparison operator on the same variable
    - Increment or decrement the same variable by a fixed value
- Otherwise, the transpiler will throw an error.
- **VALID:** `for (int i = 0; i < 3; i++) {...}`
- **VALID:** `for (i = 12; i >= foo + 3; i -= 2) {...}`
- **INVALID:** `for (int i = 0; j < 3; i++) {...}`
- **INVALID:** `for (int i = 0; i < 3; i *= 3) {...}`

## Other
- RoboBlocky cannot utilize the return value of variable assignment or unary operators ++ and --
- array is a reserved keyword