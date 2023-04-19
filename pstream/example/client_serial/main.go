package main

import (
	"bytes"
	"crypto/tls"
	"flag"
	"io"
	"log"
	"net/http"
	"os"
	// "sort"
	"strconv"
	"sync"
	"time"

	quic "github.com/lucas-clemente/pstream"
	"golang.org/x/net/http2"

	"github.com/lucas-clemente/pstream/h2quic"
	"github.com/lucas-clemente/pstream/internal/utils"
)

type orderURL struct {
	url      string
	priority uint8
}

func main() {
	verbose := flag.Bool("v", false, "verbose")
	multipath := flag.Bool("m", false, "multipath")
	output := flag.String("o", "", "logging output")
	cache := flag.Bool("c", false, "cache handshake information")
	pathScheduler := flag.String("ps", "", "path scheduler")

	flag.Parse()
	urlsSetting := flag.Args()

	if *verbose {
		utils.SetLogLevel(utils.LogLevelDebug)
	} else {
		utils.SetLogLevel(utils.LogLevelInfo)
	}

	if *output != "" {
		logfile, err := os.Create(*output)
		if err != nil {
			panic(err)
		}
		defer logfile.Close()
		log.SetOutput(logfile)
	}

	quicConfig := &quic.Config{
		CreatePaths:    *multipath,
		CacheHandshake: *cache,
		PathScheduler:  *pathScheduler,
	}

	var (
		orderURLs []orderURL //from priority low to high
		weightURL map[string]uint8
		// depURL    map[string]uint32

		priorityURL map[string]*http2.PriorityParam
	)
	tempkey := ""
	weightURL = make(map[string]uint8)
	// depURL = make(map[string]uint32)
	priorityURL = make(map[string]*http2.PriorityParam)
	utils.Infof("zy: urlsSetting: %v", urlsSetting)
	// parse URL and its corresponding priority
	for i, item := range urlsSetting {

		if i%3 == 0 {
			tempkey = item

		} else if i%3 == 1 {
			temp, err := strconv.ParseUint(item, 10, 32)
			if err != nil {
				panic(err)
			}

			weightURL[tempkey] = uint8(temp)
			priority := http2.PriorityParam{Weight: uint8(temp)}

			priorityURL[tempkey] = &priority

		} else {
			streamDep, err := strconv.ParseUint(item, 10, 32)
			if err != nil {
				panic(err)
			}

			// depURL[tempkey] = uint32(streamDep)
			priorityURL[tempkey].StreamDep = uint32(streamDep)
			if tempkey != "https://10.1.0.1:6121/randompre" {
				orderURLs = append(orderURLs, orderURL{tempkey, weightURL[tempkey]})
			}

		}
	}
	//zy set preurl
	weightURL["https://10.1.0.1:6121/randompre"] = uint8(1)
	priority := http2.PriorityParam{Weight: uint8(1)}
	priorityURL["https://10.1.0.1:6121/randompre"] = &priority
	priorityURL["https://10.1.0.1:6121/randompre"].StreamDep = uint32(0)

	// for url, pr := range weightURL {
	// 	utils.Debugf("Parse result weightURL")
	// 	utils.Debugf("Parse result: url %s, Weight %d\n", url, pr)
	// 	//zy donot append preurl into orderurl
	// 	if url != "https://10.1.0.1:6121/randompre" {
	// 		orderURLs = append(orderURLs, orderURL{url, pr})
	// 	}

	// }

	//sort with priority order from low to high
	// sort.Slice(orderURLs, func(i, j int) bool {
	// 	return orderURLs[i].priority < orderURLs[j].priority
	// })

	hclient := &http.Client{
		Transport: &h2quic.RoundTripper{QuicConfig: quicConfig, PriorityURL: priorityURL, TLSClientConfig: &tls.Config{InsecureSkipVerify: true}},
	}
	//zy create a waitgroup to block othergoroutine prefetch
	var wgpre sync.WaitGroup
	wgpre.Add(1)
	go func() {
		prestart := time.Now()
		prersp, preerr := hclient.Get("https://10.1.0.1:6121/randompre")
		if utils.Debug() {
			utils.Debugf("get prefile")
		}
		if preerr != nil {
			panic(preerr)
		}
		body := &bytes.Buffer{}
		_, preerr = io.Copy(body, prersp.Body)
		if preerr != nil {
			panic(preerr)
		}
		preelapsed := time.Since(prestart)
		utils.Infof("zypre%s: %s", prestart, preelapsed)
		wgpre.Done()
	}()
	wgpre.Wait()
	//zy serial get
	begin := time.Now()
	for _, orderURL := range orderURLs {
		addr := orderURL.url
		prio := priorityURL[addr].Weight
		utils.Infof("GET %s, priority %d", addr, prio)
		start := time.Now()
		if utils.Debug() {
			utils.Debugf("Start time of file %s: %s\n", addr, start.String())
		}
		rsp, err := hclient.Get(addr)
		if err != nil {
			panic(err)
		}

		body := &bytes.Buffer{}
		_, err = io.Copy(body, rsp.Body)
		if err != nil {
			panic(err)
		}
		elapsed := time.Since(start)
		utils.Infof("%s: %s", addr, elapsed)
	}
	completion := time.Since(begin)
	utils.Infof("Completed all: %s", completion)

}
