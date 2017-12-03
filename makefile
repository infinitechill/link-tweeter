# infinite chill / 2017
all: link-tweeter

link-tweeter: link-tweeter.py
	cp link-tweeter.py link-tweeter
	chmod u+x link-tweeter

test:
	./link-tweeter 'config.json'	

run:
	./link-tweeter 'config.json' 2>&1 &

clean:
	rm -r -f link-tweeter
	clear
