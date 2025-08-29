import React, { useState } from "react";
import "./Home.css";
import person1 from "../../assets/male.jpg";
import person2 from "../../assets/male2.jpg";
import person3 from "../../assets/female.jpeg";
import garment1 from "../../assets/trouser.jpeg";
import garment2 from "../../assets/woman.png";
import garment3 from "../../assets/shirt.jpg";
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
        <h1>Virtual Fashion Experience</h1>
        <p className="hero-subtitle">Try on clothes virtually with our AI-powered technology</p>
        <div className="features-grid">
          <div className="feature">
            <FaCamera className="feature-icon" />
            <h3>Upload Photos</h3>
            <p>Upload your photo and any clothing item</p>
          </div>
          <div className="feature">
            <FaTshirt className="feature-icon" />
            <h3>Virtual Try-On</h3>
            <p>See how clothes look on you instantly</p>
          </div>
          <div className="feature">
            <FaMagic className="feature-icon" />
            <h3>AI-Powered</h3>
            <p>Advanced AI for realistic results</p>
          </div>
          <div className="feature">
            <FaHeart className="feature-icon" />
            <h3>Save Favorites</h3>
            <p>Keep track of your favorite looks</p>
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