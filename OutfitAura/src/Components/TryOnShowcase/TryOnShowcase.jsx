import React, { useState } from "react";
import "./TryOnShowcase.css";
import beforeImg from "../../assets/before.png";
import afterImg from "../../assets/after.png";
import { Link } from "react-scroll";
import { Link as RouterLink } from "react-router-dom";



const TryOnShowcase = () => (
  <section className="tryon-showcase">
    <div className="tryon-images">
      <div className="tryon-image-container">
        <img src={beforeImg} alt="Before" />
      </div>
      <div className="tryon-image-container">
        <img src={afterImg} alt="After" />
      </div>
    </div>
    <div className="tryon-content">
      <h2>Virtual Try on Clothes With AI Magic</h2>
      <p>
      Step into the future of styling with our <b><u>AI Fashion Try-On & Assistant</u></b>. Powered by advanced computer vision and natural language processing, our system lets you upload outfits and see how they look on you — instantly. Chat with our smart assistant for personalized clothing suggestions, and experience virtual try-ons without stepping out of your home.
      </p>
      <button className="tryon-btn">Try on Clothes</button>
    </div>
  </section>
);




export default TryOnShowcase; 