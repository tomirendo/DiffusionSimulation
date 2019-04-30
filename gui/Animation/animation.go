package main

import ("fmt")
import "encoding/json"
import "io/ioutil"
import "os"
import "log"
import "math"
import "sync"
import "C"


type Molecule struct{
    Start_frame int
    Positions [][]float64
    Intensity float64
}

type Simulation struct{
    Number_of_frames int 
    Number_of_subframes_per_frame int 

    Pixel_length_in_um float64
    Psf_sigma_in_um_x_axis float64 
    Psf_sigma_in_um_y_axis float64

    Screen_size_in_pixels_x int
    Screen_size_in_pixels_y int
    
    Background_noise_amplitude float64

    Molecules []Molecule 
}

func get_position_in_frame(molecule Molecule, position_index int) []float64{
    if position_index - molecule.Start_frame < 0{
        return nil
    }
    if len(molecule.Positions) <= position_index - molecule.Start_frame{
        return nil
    }
    return molecule.Positions[position_index - molecule.Start_frame]
}

var Frames [][][]float64
var simulation Simulation


func PSF(position []float64, x float64, y float64, sigma_x float64, sigma_y float64, intensity float64) float64{
    x0 := position[0]
    y0 := position[1]
    // return 1/(2*math.Pi*sigma_x*sigma_y)*math.Exp(- math.Pow((x-x0),2)/(2*math.Pow(sigma_x,2)))*math.Exp(-math.Pow((y-y0),2)/(2*math.Pow(sigma_y,2)))

    // Max Value of 1 (not normalized)
    return intensity * math.Exp(- math.Pow((x-x0),2)/(2*math.Pow(sigma_x,2)))*math.Exp(-math.Pow((y-y0),2)/(2*math.Pow(sigma_y,2)))
}

func add_molecule_at_position_to_frame(position []float64, intensity float64, frame_index int){

    x0 := position[0]
    y0 := position[1]


    n_sigmas_x := 5 * (math.Round(simulation.Psf_sigma_in_um_x_axis/simulation.Pixel_length_in_um)+1)
    n_sigmas_y := 5 * (math.Round(simulation.Psf_sigma_in_um_y_axis/simulation.Pixel_length_in_um)+1)

    min_x_pixel := math.Max(math.Round((x0)/simulation.Pixel_length_in_um)-n_sigmas_x, 0)
    max_x_pixel := int(math.Min(math.Round((x0)/simulation.Pixel_length_in_um)+n_sigmas_x, float64(simulation.Screen_size_in_pixels_x)))

    min_y_pixel := math.Max(math.Round((y0)/simulation.Pixel_length_in_um)-n_sigmas_y, 0)
    max_y_pixel := int(math.Min(math.Round((y0)/simulation.Pixel_length_in_um)+n_sigmas_y, float64(simulation.Screen_size_in_pixels_y)))


    for i:=int(min_x_pixel); i < max_x_pixel; i++{
        for j:=int(min_y_pixel); j< max_y_pixel;j++{
            x := float64(i) * simulation.Pixel_length_in_um
            y := float64(j) * simulation.Pixel_length_in_um
            Frames[frame_index][i][j] += PSF(position, x, y, simulation.Psf_sigma_in_um_x_axis, simulation.Psf_sigma_in_um_y_axis, intensity)

        } 
    }
}

func create_frame(frame_index int, wg *sync.WaitGroup){
    for _, molecule := range simulation.Molecules{
        for subframe:=0; subframe < simulation.Number_of_subframes_per_frame; subframe++{
            subframe_index := frame_index*simulation.Number_of_subframes_per_frame + subframe
            position := get_position_in_frame(molecule,subframe_index) 
            if position != nil{
                add_molecule_at_position_to_frame(position, molecule.Intensity, frame_index)
            }
        }
    }

    json_data, _ := json.Marshal(Frames[frame_index])
    err := ioutil.WriteFile(fmt.Sprintf("%d.json", frame_index), json_data, 0644)
    check(err)
    Frames[frame_index] = nil
    defer wg.Done()
}

func check(err error){
    if err != nil {
        log.Fatal(err)
    }
}
//export createAnimation
func createAnimation(temp_file string){
    // Receives JSON formatted data 
    jsonFile, err := os.Open("_temp_animation_file.json")
    // if we os.Open returns an error then handle it
    check(err)
    
    // defer the closing of our jsonFile so that we can parse it later on
    defer jsonFile.Close()
    byteValue, _ := ioutil.ReadAll(jsonFile)
    err = json.Unmarshal([]byte(byteValue), &simulation)
    // err := json.Unmarshal([]byte(data), &simulation)
    check(err)
    

    Frames = make([][][]float64, simulation.Number_of_frames)
    for i:=0; i<simulation.Number_of_frames; i++{
        Frames[i] = make([][]float64, simulation.Screen_size_in_pixels_x)
        for j:=0; j<simulation.Screen_size_in_pixels_x; j++{
            Frames[i][j] = make([]float64, simulation.Screen_size_in_pixels_y)
        }
    }

    var wg sync.WaitGroup
    wg.Add(simulation.Number_of_frames)

    for i:= 0; i< simulation.Number_of_frames; i++{
        go create_frame(i, &wg)
        // if (i % 100 == 0) && (i != 0) {
        //     wg.Wait()
        // }
    }

    wg.Wait()

    // json_data, _ := json.Marshal(Frames)
    // Frames = nil
    // err = ioutil.WriteFile("/tmp/_temp_animation_frames.json", json_data, 0644)
    // check(err)

}

func main(){
    fmt.Println("You should compile not RUN!")
}