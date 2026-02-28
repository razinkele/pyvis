@echo off
python -m pip install . -vv --no-deps --no-build-isolation
if errorlevel 1 exit 1

python -c "import shutil, os, glob; share=os.path.join(os.environ['PREFIX'],'share','pyvis'); [os.makedirs(os.path.join(share,d),exist_ok=True) for d in ('examples','notebooks')]; [shutil.copy2(f,os.path.join(share,'examples')) for f in glob.glob('examples/*.py')]; [shutil.copy2(f,os.path.join(share,'notebooks')) for f in glob.glob('notebooks/*.ipynb')+glob.glob('notebooks/*.csv')+glob.glob('notebooks/*.dot')]"
if errorlevel 1 exit 1
