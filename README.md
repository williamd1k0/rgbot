# RGBot :rooster: (Rinha de Galo BOT)

![heroku](devel/heroku.png)
![python](https://img.shields.io/badge/python-3.5%2B-blue.svg?style=flat-square)
![godot](https://img.shields.io/badge/Godot-3.1%2B-blue.svg?style=flat-square)
![license](https://img.shields.io/badge/License-Meteor-lightgray.svg?style=flat-square)

## Introdução

>**NÃO APOIAMOS RINHA DE GALO REAL. NÃO PARTICIPE DE ATIVIDADES ILÍCITAS.**

**Rinha de Galo Bot** é um bot automático onde dois galos aleatoriamente gerados/selecionados são postos para lutar em turnos.
Por ser automático, você não pode influenciar a luta - apenas torça pelo seu galo favorito!

## Como funciona?

- Dois galos são gerados, com **Vitalidade**, **Pontos de Ataque** e **quatro ataques**;
- O bot seleciona, aleatoriamente, um dos galos para atacar o outro;
- O bot seleciona, aleatoriamente, um dos ataques do galo escolhido;
- Cada ataque tem um valor de Pontos de Ataque que são gastos quando usado;
- Se o ataque escolhido não puder ser realizado por falta de Pontos de Ataque, o galo não ataca e perde um turno;
- Vence quem fizer o outro galo perder completamente a Vitalidade.

## Contas ativas

Mastodon: https://botsin.space/@rgbot

Twitter: *Em breve*

## Desenvolvimento

### Servidor

- Python 3.5+
- PostgreSQL (ou SQLite3)

## Bibliotecas

- pony (ORM/Banco de dados)
- pillow (Manipulador de imagens)
- psycopg2 (PostgreSQL para Python )- tweepy (Twitter API)
- Mastodon.py (Mastodon API)
