program Saudacao;

procedure MostrarSaudacao(nome: string);
begin
  writeln('Olá, ', nome, '! Seja bem-vindo ao programa em Pascal.');
end;

var
  nomeUsuario: string;

begin
  writeln('Digite seu nome:');
  readln(nomeUsuario);
  MostrarSaudacao(nomeUsuario);
end.