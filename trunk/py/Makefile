all: cur

clean:
	rm -f *~ *.pyc
	(cd test && rm -f *~ *.pyc)

code:
	gvim -S Session.vim &

cur:
	(cd test && python test.py -l file.Test.test_chunk)

.PHONY: test
