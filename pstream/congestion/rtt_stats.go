package congestion

import (
	"time"

	"github.com/lucas-clemente/pstream/internal/protocol"
	"github.com/lucas-clemente/pstream/internal/utils"
)

const (
	initialRTTus          = 100 * 1000
	rttAlpha      float32 = 0.125
	oneMinusAlpha float32 = (1 - rttAlpha)
	rttBeta       float32 = 0.25
	oneMinusBeta  float32 = (1 - rttBeta)
	halfWindow    float32 = 0.5
	quarterWindow float32 = 0.25
	gradientScale         = 100
)

type rttSample struct {
	rtt  time.Duration
	time time.Time
}

// RTTStats provides round-trip statistics
type RTTStats struct {
	initialRTTus int64

	recentMinRTTwindow time.Duration
	minRTT             time.Duration
	latestRTT          time.Duration
	smoothedRTT        time.Duration
	meanDeviation      time.Duration
	gradientRTT        time.Duration //ytxing
	deltaRTT           time.Duration //ytxing
	deltaMinRTT        time.Duration //ytxing

	recentcwndMinRTT                 time.Duration //zy
	lastcwndMinRTT                   time.Duration //zy
	timefornumMinRTTsamplesRemaining time.Time     //zy
	timeforrecentcwndMinRTT          time.Time     //zy
	timeforlastcwndMinRTT            time.Time     //zy

	numMinRTTsamplesRemaining protocol.PacketNumber

	newMinRTT        rttSample
	recentMinRTT     rttSample
	halfWindowRTT    rttSample
	quarterWindowRTT rttSample
}

// NewRTTStatsWithSmoothedRTT makes a properly initialized Smoothed RTTStats object
func NewRTTStatsWithSmoothedRTT(smoothedRTT time.Duration) *RTTStats {
	return &RTTStats{
		smoothedRTT: smoothedRTT,
	}
}

// NewRTTStats makes a properly initialized RTTStats object
func NewRTTStats() *RTTStats {
	return &RTTStats{
		initialRTTus:       initialRTTus,
		recentMinRTTwindow: utils.InfDuration,
	}
}

// InitialRTTus is the initial RTT in us
func (r *RTTStats) InitialRTTus() int64 { return r.initialRTTus }

// MinRTT Returns the minRTT for the entire connection.
// May return Zero if no valid updates have occurred.
func (r *RTTStats) MinRTT() time.Duration { return r.minRTT }

// LatestRTT returns the most recent rtt measurement.
// May return Zero if no valid updates have occurred.
func (r *RTTStats) LatestRTT() time.Duration { return r.latestRTT }

// RecentMinRTT the minRTT since SampleNewRecentMinRtt has been called, or the
// minRTT for the entire connection if SampleNewMinRtt was never called.
func (r *RTTStats) RecentMinRTT() time.Duration { return r.recentMinRTT.rtt }

// SmoothedRTT returns the EWMA smoothed RTT for the connection.
// May return Zero if no valid updates have occurred.
func (r *RTTStats) SmoothedRTT() time.Duration { return r.smoothedRTT }

// GetQuarterWindowRTT gets the quarter window RTT
func (r *RTTStats) GetQuarterWindowRTT() time.Duration { return r.quarterWindowRTT.rtt }

// GetHalfWindowRTT gets the half window RTT
func (r *RTTStats) GetHalfWindowRTT() time.Duration { return r.halfWindowRTT.rtt }

// MeanDeviation gets the mean deviation
func (r *RTTStats) MeanDeviation() time.Duration { return r.meanDeviation }

// GetGradientRTT gets the gradient of RTT ytxing
func (r *RTTStats) GetGradientRTT() time.Duration { return r.gradientRTT }

// GetDeltaRTT gets the difference of recent two sommthed RTT
func (r *RTTStats) GetDeltaRTT() time.Duration { return r.deltaRTT }

// GetDeltaRTT gets the difference of recent minRTT
func (r *RTTStats) GetDeltaMinRTT() time.Duration { return r.deltaMinRTT }

// SetRecentMinRTTwindow sets how old a recent min rtt sample can be.
func (r *RTTStats) SetRecentMinRTTwindow(recentMinRTTwindow time.Duration) {
	r.recentMinRTTwindow = recentMinRTTwindow
}

// zy getrecentminrttwindow
func (r *RTTStats) RecentMinRTTwindow() time.Duration { return r.recentMinRTTwindow }

//zy getnumMinRTTsamplesremaining
func (r *RTTStats) NumMinRTTsamplesRemaining() protocol.PacketNumber {
	return r.numMinRTTsamplesRemaining
}

//zy gettimefornumMinRTTsamplesRemaining
func (r *RTTStats) TimefornumMinRTTsamplesRemaining() time.Time {
	return r.timefornumMinRTTsamplesRemaining
}

//zy setTimefornumMinRTTsamplesRemaining
func (r *RTTStats) SettimefornumMinRTTsamplesRemaining(now time.Time) {
	r.timefornumMinRTTsamplesRemaining = now
}

//zy getrecentcwndminrtt
func (r *RTTStats) RecentcwndMinRTT() time.Duration {
	return r.recentcwndMinRTT
}

//zy setrecentcwndminRTT
func (r *RTTStats) SetrecentcwndminRTT(minRTT time.Duration) {
	r.recentcwndMinRTT = minRTT
}

//zy getlastcwndminrtt
func (r *RTTStats) LastcwndMinRTT() time.Duration {
	return r.lastcwndMinRTT
}

//zy setrecentcwndminRTT
func (r *RTTStats) SetlastcwndminRTT(minRTT time.Duration) {
	r.lastcwndMinRTT = minRTT
}

// UpdateRTT updates the RTT based on a new sample.
func (r *RTTStats) UpdateRTT(sendDelta, ackDelay time.Duration, now time.Time) {
	if sendDelta == utils.InfDuration || sendDelta <= 0 {
		utils.Debugf("Ignoring measured sendDelta, because it's is either infinite, zero, or negative: %d", sendDelta/time.Microsecond)
		return
	}

	// Update r.minRTT first. r.minRTT does not use an rttSample corrected for
	// ackDelay but the raw observed sendDelta, since poor clock granularity at
	// the client may cause a high ackDelay to result in underestimation of the
	// r.minRTT.
	if r.minRTT == 0 || r.minRTT > sendDelta {
		r.minRTT = sendDelta
	}
	r.deltaMinRTT = r.RecentMinRTT()
	//sinceTime := time.Since(r.recentMinRTT.time) //zy change
	r.updateRecentMinRTT(sendDelta, now)
	r.deltaMinRTT = r.RecentMinRTT() - r.deltaMinRTT
	//r.gradientRTT = (r.deltaMinRTT * gradientScale) / sinceTime //ytxing: maybe some check when <0? //zy change

	// Correct for ackDelay if information received from the peer results in a
	// positive RTT sample. Otherwise, we use the sendDelta as a reasonable
	// measure for smoothedRTT.
	sample := sendDelta
	if sample > ackDelay {
		sample -= ackDelay
	}
	r.latestRTT = sample
	// First time call.
	if r.smoothedRTT == 0 {
		r.smoothedRTT = sample
		r.meanDeviation = sample / 2 //zy 111
		// r.gradientRTT = 0 //zy change
	} else {
		r.meanDeviation = time.Duration(oneMinusBeta*float32(r.meanDeviation/time.Microsecond)+rttBeta*float32(utils.AbsDuration(r.smoothedRTT-sample)/time.Microsecond)) * time.Microsecond
		r.deltaRTT = r.smoothedRTT
		r.smoothedRTT = time.Duration((float32(r.smoothedRTT/time.Microsecond)*oneMinusAlpha)+(float32(sample/time.Microsecond)*rttAlpha)) * time.Microsecond
		r.deltaRTT = r.smoothedRTT - r.deltaRTT
		// r.gradientRTT = (r.deltaRTT * gradientScale) / sample
	}
	utils.Debugf("ytxing: in rtt_stat.go smoothedRTT Updated sample %v smoothedRTT %v, meanDeviation %v, gradientRTT %v， deltaMinRTT %v", sample, r.smoothedRTT, r.meanDeviation, r.gradientRTT, r.deltaMinRTT)
}

// zy updaterecentcwndMinRTT,zeroflag = 0 means next cwnd
func (r *RTTStats) UpdaterecentcwndMinRTT(sendDelta, ackDelay time.Duration, zeroflag bool) {
	sample := sendDelta
	if sample > ackDelay {
		sample -= ackDelay
	}
	if r.recentcwndMinRTT == 0 || sample <= r.recentcwndMinRTT {
		r.recentcwndMinRTT = sample
		r.timeforrecentcwndMinRTT = time.Now()
		utils.Debugf("zy:updaterecentcwndminRTT %v", r.recentcwndMinRTT)
	}
	if !zeroflag {
		r.lastcwndMinRTT = r.recentcwndMinRTT
		r.timeforlastcwndMinRTT = r.timeforrecentcwndMinRTT
		r.recentcwndMinRTT = 0
		utils.Debugf("zy:updatelastcwndminRTT %v", r.lastcwndMinRTT)
	}
	if r.lastcwndMinRTT != 0 && r.recentcwndMinRTT != 0 {
		deltacwndMinRTT := r.recentcwndMinRTT - r.lastcwndMinRTT
		timeduration := r.timeforrecentcwndMinRTT.Sub(r.timeforlastcwndMinRTT)
		floatgradient := float64((deltacwndMinRTT)) / (float64(timeduration))
		r.gradientRTT = time.Duration(float64((deltacwndMinRTT)) / (float64(timeduration)))

		utils.Debugf("zy:recentcwndMinRTT %v, lastcwndMinRTT %v, floatgradient %v, updategradientRTT %v", r.recentcwndMinRTT, float64(r.lastcwndMinRTT), floatgradient, r.gradientRTT)
	}
}
func (r *RTTStats) updateRecentMinRTT(sample time.Duration, now time.Time) { // Recent minRTT update.
	utils.Debugf("zy:numMinRTTsamplesRemaining %v, recentMinRTTwindow %v", r.numMinRTTsamplesRemaining, r.recentMinRTTwindow)
	// if r.numMinRTTsamplesRemaining > 0 {
	// 	r.numMinRTTsamplesRemaining--
	// 	if r.newMinRTT.rtt == 0 || sample <= r.newMinRTT.rtt {
	// 		r.newMinRTT = rttSample{rtt: sample, time: now}
	// 	}
	// 	if r.numMinRTTsamplesRemaining == 0 {
	// 		r.recentMinRTT = r.newMinRTT
	// 		r.halfWindowRTT = r.newMinRTT
	// 		r.quarterWindowRTT = r.newMinRTT
	// 	}
	// }

	utils.Debugf("zy:before update recentMinRTT %v", r.recentMinRTT.rtt)
	// Update the three recent rtt samples.
	if r.recentMinRTT.rtt == 0 || sample <= r.recentMinRTT.rtt {
		r.recentMinRTT = rttSample{rtt: sample, time: now}
		r.halfWindowRTT = r.recentMinRTT
		r.quarterWindowRTT = r.recentMinRTT
	} else if sample <= r.halfWindowRTT.rtt {
		r.halfWindowRTT = rttSample{rtt: sample, time: now}
		r.quarterWindowRTT = r.halfWindowRTT
	} else if sample <= r.quarterWindowRTT.rtt {
		r.quarterWindowRTT = rttSample{rtt: sample, time: now}
	}

	// Expire old min rtt samples.
	utils.Debugf("zy:before expire recentMinRTT %v", r.recentMinRTT.rtt)
	if r.recentMinRTT.time.Before(now.Add(-r.recentMinRTTwindow)) {
		r.recentMinRTT = r.halfWindowRTT
		r.halfWindowRTT = r.quarterWindowRTT
		r.quarterWindowRTT = rttSample{rtt: sample, time: now}
	} else if r.halfWindowRTT.time.Before(now.Add(-time.Duration(float32(r.recentMinRTTwindow/time.Microsecond)*halfWindow) * time.Microsecond)) {
		r.halfWindowRTT = r.quarterWindowRTT
		r.quarterWindowRTT = rttSample{rtt: sample, time: now}
	} else if r.quarterWindowRTT.time.Before(now.Add(-time.Duration(float32(r.recentMinRTTwindow/time.Microsecond)*quarterWindow) * time.Microsecond)) {
		r.quarterWindowRTT = rttSample{rtt: sample, time: now}
	}
	utils.Debugf("zy:after expire recentMinRTT %v", r.recentMinRTT.rtt)
}

// SampleNewRecentMinRTT forces RttStats to sample a new recent min rtt within the next
// |numSamples| UpdateRTT calls.
func (r *RTTStats) SampleNewRecentMinRTT(numSamples protocol.PacketNumber) {
	r.numMinRTTsamplesRemaining = numSamples
	r.newMinRTT = rttSample{}
}

//zy setnumMinRTTsamplesRemaining
func (r *RTTStats) SetnumMinRTTsamplesRemaining(numSamples protocol.PacketNumber) {
	r.numMinRTTsamplesRemaining = numSamples
}

// OnConnectionMigration is called when connection migrates and rtt measurement needs to be reset.
func (r *RTTStats) OnConnectionMigration() {
	r.latestRTT = 0
	r.minRTT = 0
	r.smoothedRTT = 0
	r.meanDeviation = 0
	r.initialRTTus = initialRTTus
	r.numMinRTTsamplesRemaining = 0
	r.recentMinRTTwindow = utils.InfDuration
	r.recentMinRTT = rttSample{}
	r.halfWindowRTT = rttSample{}
	r.quarterWindowRTT = rttSample{}
	r.timefornumMinRTTsamplesRemaining = time.Now() //zy
	utils.Debugf("zy:init timefornumMinRTTRemaining %v", r.timefornumMinRTTsamplesRemaining)
}

// ExpireSmoothedMetrics causes the smoothed_rtt to be increased to the latest_rtt if the latest_rtt
// is larger. The mean deviation is increased to the most recent deviation if
// it's larger.
func (r *RTTStats) ExpireSmoothedMetrics() {
	r.meanDeviation = utils.MaxDuration(r.meanDeviation, utils.AbsDuration(r.smoothedRTT-r.latestRTT))
	r.smoothedRTT = utils.MaxDuration(r.smoothedRTT, r.latestRTT)
}

// UpdateSessionRTT XXX (QDC): This is subject to improvement
// Update the smoothed RTT to the given value
func (r *RTTStats) UpdateSessionRTT(smoothedRTT time.Duration) {
	r.smoothedRTT = smoothedRTT
}
