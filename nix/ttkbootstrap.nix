{
  lib,
  buildPythonPackage,
  fetchurl,
  pillow,
  setuptools,
}:

buildPythonPackage rec {
  pname = "ttkbootstrap";
  version = "1.10.1";
  pyproject = false;
  format = "setuptools";

  # Bethini tracks DoubleYouC's fork rather than PyPI.
  src = fetchurl {
    url = "https://github.com/DoubleYouC/ttkbootstrap/archive/f0673254c7e6e04c85e84b145327b436c3dda394.tar.gz";
    hash = "sha256-YQf4h+60ZVgUJiXMs2snP7h+UFVnXFOt7OXlRIorMis=";
  };

  nativeBuildInputs = [ setuptools ];

  propagatedBuildInputs = [ pillow ];

  pythonRelaxDeps = [ "pillow" ];

  doCheck = false;

  meta = {
    description = "Bootstrap-inspired theme extension for tkinter (DoubleYouC fork)";
    homepage = "https://github.com/DoubleYouC/ttkbootstrap";
    license = lib.licenses.mit;
  };
}
