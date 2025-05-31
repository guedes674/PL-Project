program SumIntegersWithoutHalt;

{ 
  Este programa lê até 50 números inteiros inseridos pelo utilizador,
  chama um procedimento para calcular a soma desses valores e, em seguida,
  exibe o resultado.
  Caso o número de elementos seja inválido, exibe uma mensagem de erro
  e encerra de forma natural (sem usar HALT).
}

var
  arr: array[1..50] of Integer;
  n, i, total: Integer;

{--------------------------------------------------------------------------
  Procedure: ComputeSum
  Calcula a soma dos primeiros Count elementos de A e coloca o resultado em S.
  Parâmetros:
    var A: array[1..50] of Integer — array cujos valores serão somados.
    Count: Integer — número de elementos válidos em A (de 1 a 50).
    var S: Integer — variável onde a soma será armazenada.
--------------------------------------------------------------------------}
procedure ComputeSum(var A: array[1..50] of Integer; Count: Integer; var S: Integer);
var
  j: Integer;
begin
  S := 0;
  for j := 1 to Count do
    S := S + A[j];
end;

begin
  { Solicita ao utilizador a quantidade de números a somar }
  Write('Quantos números deseja somar (1..50)? ');
  Readln(n);
  if (n < 1) or (n > 50) then
  begin
    Writeln('Número inválido. O programa será encerrado.');
  end
  else
  begin
    { Lê os n valores inteiros }
    for i := 1 to n do
    begin
      Write('Número ', i, ': ');
      Readln(arr[i]);
    end;

    { Chama o procedimento para calcular a soma }
    ComputeSum(arr, n, total);

    { Exibe o resultado }
    Writeln('A soma dos ', n, ' valores é: ', total);
  end;
end.
