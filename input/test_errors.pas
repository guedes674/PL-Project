program TestSemanticErrors;

var
    a: integer;
    b: string;
    c: real;
    d: integer;
    e: integer;
    arr: array[1..10] of integer;

begin
    a := 5;
    b := 'Hello';
    {type mismatch}
    c := a + 2.5;
    d := arr[5];
    {Array index out of bounds}
    e := arr[11];

    {Variable not declared}
    f := 10;

    writeln(a, b);
    writeln(c, d, e);
    {Using an undeclared variable}
    {writeln(unknownVar);}

    {type mismatch in assignment}
    {a := b;}

    { Using a function with incorrect number of arguments }
    writeln(a, b, c, d);

    { Using a variable before declaration }
    {result := myFunction(a);}

end.