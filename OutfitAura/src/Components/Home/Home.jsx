import React, { useState } from "react";
import "./home.css";
import person1 from "../../assets/male.jpg";
import person2 from "../../assets/male2.jpg";
import person3 from "../../assets/female.jpeg";
import garment1 from "../../assets/trouser.jpeg";
import garment2 from "../../assets/woman.png";
import garment3 from "../../assets/shirt.jpg";
import heroImg from "../../assets/home_before_after.png";
import { FaCamera, FaTshirt, FaMagic, FaHeart } from "react-icons/fa";

const Home = () => {
  const [modelImage, setModelImage] = useState(null);
  const [garmentImage, setGarmentImage] = useState(null);
  const [resultImage, setResultImage] = useState(null);

  const handleModelUpload = (event) => {
    setModelImage(URL.createObjectURL(event.target.files[0]));
  };

  const handleGarmentUpload = (event) => {
    setGarmentImage(URL.createObjectURL(event.target.files[0]));
  };

  const handleDragStart = (event, src) => {
    event.dataTransfer.setData("imageSrc", src);
  };

  const handleDrop = (event, type) => {
    event.preventDefault();
    const imageSrc = event.dataTransfer.getData("imageSrc");
    if (imageSrc) {
      if (type === "model") setModelImage(imageSrc);
      else if (type === "garment") setGarmentImage(imageSrc);
    }
  };

  const removeImage = (type) => {
    if (type === "model") setModelImage(null);
    else if (type === "garment") setGarmentImage(null);
  };

  return (
    <div className="home-page">
      <div className="hero-section">
        <div className="hero-inner">
          <div className="hero-copy">
            <h1 className="hero-title">Redefine Fashion —<br className="hero-br" /> One Click at a Time</h1>
            <p className="hero-subtitle">Discover a smarter way to explore outfits. Our AI‑enhanced virtual studio lets you preview looks in real‑time — no fitting room, no hassle. Dress with precision and confidence, anytime, anywhere.</p>
          </div>
          <div className="hero-media">
            <div className="hero-card">
              <img src={heroImg} alt="Before and after virtual try-on" />
            </div>
          </div>
        </div>
      </div>

      <div className="try-on-section">
        <h1>Try It Now</h1>
        <p className="section-description">Upload your photo and any clothing item to see how it looks on you</p>
        
        <div className="home-container">
          {/* Model Upload Section */}
          <div className="upload-section">
            <h3>Step 1: Upload Your Photo</h3>
            <label
              className="upload-box"
              onDrop={(e) => handleDrop(e, "model")}
              onDragOver={(e) => e.preventDefault()}
            >
              <input type="file" onChange={handleModelUpload} hidden />
              {modelImage ? (
                <div className="image-preview">
                  <img src={modelImage} alt="Model" className="preview" />
                  <button className="remove-btn" onClick={() => removeImage("model")}>❌</button>
                </div>
              ) : (
                <div className="upload-placeholder">
                  <FaCamera className="upload-icon" />
                  <p>Drop or Click to Upload</p>
                </div>
              )}
            </label>
            <div className="examples">
              <h4>Example Photos</h4>
              <div className="example-list">
                {[person1, person2, person3].map((src, index) => (
                  <img
                    key={index}
                    src={src}
                    alt="Example"
                    draggable
                    onDragStart={(e) => handleDragStart(e, src)}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Garment Upload Section */}
          <div className="upload-section">
            <h3>Step 2: Upload Clothing</h3>
            <label
              className="upload-box"
              onDrop={(e) => handleDrop(e, "garment")}
              onDragOver={(e) => e.preventDefault()}
            >
              <input type="file" onChange={handleGarmentUpload} hidden />
              {garmentImage ? (
                <div className="image-preview">
                  <img src={garmentImage} alt="Garment" className="preview" />
                  <button className="remove-btn" onClick={() => removeImage("garment")}>❌</button>
                </div>
              ) : (
                <div className="upload-placeholder">
                  <FaTshirt className="upload-icon" />
                  <p>Drop or Click to Upload</p>
                </div>
              )}
            </label>
            <div className="examples">
              <h4>Example Clothing</h4>
              <div className="example-list">
                {[garment1, garment2, garment3].map((src, index) => (
                  <img
                    key={index}
                    src={src}
                    alt="Example"
                    draggable
                    onDragStart={(e) => handleDragStart(e, src)}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Result Section */}
          <div className="result-section">
            <h3>Step 3: See the Result</h3>
            <div className="result-box">
              {resultImage ? (
                <img src={resultImage} alt="Result" className="preview" />
              ) : (
                <div className="upload-placeholder">
                  <FaMagic className="upload-icon" />
                  <p>Your Virtual Try-On Result</p>
                </div>
              )}
            </div>
            <button className="result-btn">Generate Try-On</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;