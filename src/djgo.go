package main

import (
	"fmt"
	"log"
	"net/http"
	"os/exec"
	"runtime"
	"strings"

	"io/ioutil"

	"github.com/zmb3/spotify"
)

const redirectURI = "http://localhost:8080/callback"

var (
	auth  = spotify.NewAuthenticator(redirectURI, spotify.ScopeUserReadCurrentlyPlaying, spotify.ScopeUserReadPlaybackState, spotify.ScopeUserModifyPlaybackState)
	ch    = make(chan *spotify.Client)
	state = "abc123"
)

var html = `
<br/>
<a href="/player/play">Play</a><br/>
<a href="/player/pause">Pause</a><br/>
<a href="/player/next">Next track</a><br/>
<a href="/player/previous">Previous Track</a><br/>
<a href="/player/shuffle">Shuffle</a><br/>
`

func main() {
	var client *spotify.Client
	var playerState *spotify.PlayerState

	// first start an HTTP server
	http.HandleFunc("/callback", completeAuth)
	http.HandleFunc("/player/", func(w http.ResponseWriter, r *http.Request) {
		action := strings.TrimPrefix(r.URL.Path, "/player/")
		var err error
		switch action {
		case "play":
			err = client.Play()
		case "pause":
			err = client.Pause()
		case "next":
			err = client.Next()
		case "previous":
			err = client.Previous()
		case "shuffle":
			playerState.ShuffleState = !playerState.ShuffleState
			err = client.Shuffle(playerState.ShuffleState)
		}
		if err != nil {
			log.Print(err)
		}

		w.Header().Set("Content-Type", "text/html")
		fmt.Fprint(w, html)
	})
	go func() {
		auth.SetAuthInfo("fa177870e1774e51b5d541efd38a2c4d", "fcec3e19de854e4595d9bbdb1e4cc616")
		url := auth.AuthURL(state)
		open(url)

		// wait for auth to complete
		client = <-ch

		// use the client to make calls that require authorization
		user, err := client.CurrentUser()
		if err != nil {
			log.Fatal(err)
		}
		fmt.Println("Hello, " + user.ID + "! Welcome to DJ Go!")

		playerState, err = client.PlayerState()
		if err != nil {
			log.Fatal(err)
		}
		if playerState.Device.Type == "" {
			fmt.Println("No device detected, please start playing spotify...")
		} else {
			fmt.Printf("Found your %s (%s)\n", playerState.Device.Type, playerState.Device.Name)
		}
	}()

	http.ListenAndServe(":8080", nil)

	for {
		_, err := ioutil.ReadFile("./emotion.txt")
		check(err)
		//fmt.Print(string(dat))
	}
}

func completeAuth(w http.ResponseWriter, r *http.Request) {
	tok, err := auth.Token(state, r)
	if err != nil {
		http.Error(w, "Couldn't get token", http.StatusForbidden)
		log.Fatal(err)
	}
	if st := r.FormValue("state"); st != state {
		http.NotFound(w, r)
		log.Fatalf("State mismatch: %s != %s\n", st, state)
	}
	// use the token to get an authenticated client
	client := auth.NewClient(tok)
	w.Header().Set("Content-Type", "text/html")
	fmt.Fprintf(w, "Login Completed!"+html)
	ch <- &client
}

// open opens the specified URL in the default browser of the user.
func open(url string) error {
	var cmd string
	var args []string

	switch runtime.GOOS {
	case "windows":
		cmd = "cmd"
		args = []string{"/c", "start"}
	case "darwin":
		cmd = "open"
	default: // "linux", "freebsd", "openbsd", "netbsd"
		cmd = "xdg-open"
	}
	args = append(args, url)
	return exec.Command(cmd, args...).Start()
}

func check(e error) {
	if e != nil {
		panic(e)
	}
}
