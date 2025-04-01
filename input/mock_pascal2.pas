program SumFunctionExample;

function Sum(a, b: Integer): Integer;
begin
  Sum := a + b;
end;

var
  num1, num2, result: Integer;
begin
  Write('Enter first number: ');
  ReadLn(num1);
  Write('Enter second number: ');
  ReadLn(num2);
  
  result := Sum(num1, num2);
  
  WriteLn('The sum is: ', result);
end.