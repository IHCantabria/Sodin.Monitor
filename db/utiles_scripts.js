db.postEventos.aggregate()
      .match(qb.where("idEstacion").eq("Q104"))
      .project({
         items: {
            $filter: {
               input: "$tweets",
               as: "tweet",
               cond: { $eq: [ "$$tweet.id_tweet", '1088251108072570881' ] }
            }
         }
      }
      //.unwind("$arrayField")
      //.group({ _id: "", count: { $sum: 1 } })
      //.sort("-count")
      //.limit(5)