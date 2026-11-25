from packaging.requirements import Requirement

from hatchling.cli.dep.core import DistributionCache, dependency_in_sync


def test_extra_with_no_requirements(tmp_path):
    dist_info = tmp_path / "coverage-7.17.5.dist-info"
    dist_info.mkdir()
    (dist_info / "METADATA").write_text(
        "Metadata-Version: 2.1\nName: coverage\nVersion: 7.17.5\nProvides-Extra: toml\n",
        encoding="utf-8",
    )

    distributions = DistributionCache([str(tmp_path)])

    assert dependency_in_sync(Requirement("coverage[toml]"), {}, distributions)
    assert not dependency_in_sync(Requirement("coverage[unknown]"), {}, distributions)
