from main import main


def test_main_prints_success(capsys):
    main()
    assert "Databricks" in capsys.readouterr().out
