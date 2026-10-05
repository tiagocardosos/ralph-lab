"""`python3 -m pipeline`: roda join -> pivot -> pagina e regenera os tres entregaveis."""

from pipeline import join, pagina, pivot


def main():
    join.main()
    pivot.main()
    pagina.main()


if __name__ == "__main__":
    main()
