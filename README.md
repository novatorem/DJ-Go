# DJ-Go

## Requirements

### [Go](https://golang.org/dl/) 

* `export GOPATH="$HOME/go"`
* `export PATH="$PATH:$GOPATH/bin"`

* `go get -u -f github.com/esimov/pigo/cmd/pigo`
* `go install`

### [Python2](https://www.python.org/downloads/release/python-2718/)

* `pip install numpy`
* `pip install opencv-python`
* `pip install opencv-python-headless`

## Running

`python2 djgo.go`

### Keys:
<kbd>w</kbd> - Show/hide detected faces (default Off)<br/>
<kbd>e</kbd> - Show/hide detected pupils (default On)<br/>
<kbd>e</kbd> - Show/hide facial landmark points (default On)<br/>
<kbd>q</kbd> - Quit